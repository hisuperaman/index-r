from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from iam.models import User

EMAIL = "ada@example.com"
PASSWORD = "an-uncommon-passphrase"


class JWTLoginTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email=EMAIL, password=PASSWORD)
		EmailAddress.objects.create(user=cls.user, email=EMAIL, verified=True, primary=True)

	def login(self, email=EMAIL, password=PASSWORD):
		return self.client.post(reverse("rest_login"), {"email": email, "password": password})

	def refresh(self, refresh_token):
		return self.client.post(reverse("token_refresh"), {"refresh": refresh_token})

	def get_user(self, access_token=None):
		if access_token:
			self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
		return self.client.get(reverse("rest_user_details"))

	def test_login_returns_access_and_refresh_tokens(self):
		response = self.login()

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["access"])
		self.assertTrue(response.data["refresh"])
		self.assertEqual(response.data["user"]["email"], EMAIL)

	def test_login_starts_no_session(self):
		self.login()

		self.assertNotIn("sessionid", self.client.cookies)

	def test_wrong_password_is_rejected(self):
		response = self.login(password="wrong-password")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("non_field_errors", response.data)

	def test_unverified_email_is_rejected(self):
		EmailAddress.objects.filter(user=self.user).update(verified=False)

		response = self.login()

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_access_token_authenticates_requests(self):
		response = self.get_user(self.login().data["access"])

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["email"], EMAIL)

	def test_request_without_token_is_unauthorized(self):
		self.assertEqual(self.get_user().status_code, status.HTTP_401_UNAUTHORIZED)

	def test_invalid_access_token_is_unauthorized(self):
		self.assertEqual(self.get_user("not-a-jwt").status_code, status.HTTP_401_UNAUTHORIZED)

	def test_refresh_rotates_the_refresh_token(self):
		refresh_token = self.login().data["refresh"]

		response = self.refresh(refresh_token)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["access"])
		self.assertNotEqual(response.data["refresh"], refresh_token)
		self.assertEqual(self.get_user(response.data["access"]).status_code, status.HTTP_200_OK)

	def test_rotated_refresh_token_cannot_be_reused(self):
		refresh_token = self.login().data["refresh"]
		self.refresh(refresh_token)

		self.assertEqual(self.refresh(refresh_token).status_code, status.HTTP_401_UNAUTHORIZED)

	def test_logout_blacklists_the_refresh_token(self):
		tokens = self.login().data
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

		response = self.client.post(reverse("rest_logout"), {"refresh": tokens["refresh"]})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(self.refresh(tokens["refresh"]).status_code, status.HTTP_401_UNAUTHORIZED)


class UserDetailsTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email=EMAIL, password=PASSWORD)

	def setUp(self):
		self.client.force_authenticate(self.user)

	def test_returns_the_profile(self):
		response = self.client.get(reverse("rest_user_details"))

		self.assertEqual(response.data, {
			"id": self.user.id, "email": EMAIL, "has_password": True, "first_name": "", "last_name": "",
		})

	def test_a_user_without_a_password_is_flagged(self):
		self.user.set_unusable_password()
		self.user.save()

		self.assertFalse(self.client.get(reverse("rest_user_details")).data["has_password"])

	def test_updates_the_name_but_not_the_email(self):
		response = self.client.patch(
			reverse("rest_user_details"), {"first_name": "Ada", "last_name": "Lovelace", "email": "new@example.com"},
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.user.refresh_from_db()
		self.assertEqual((self.user.first_name, self.user.last_name, self.user.email), ("Ada", "Lovelace", EMAIL))


class PasswordChangeTests(APITestCase):
	NEW_PASSWORD = "a-different-passphrase"

	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email=EMAIL, password=PASSWORD)

	def setUp(self):
		self.client.force_authenticate(self.user)

	def change(self, **data):
		return self.client.post(reverse("rest_password_change"), {
			"new_password1": self.NEW_PASSWORD, "new_password2": self.NEW_PASSWORD, **data,
		})

	def test_changes_the_password_given_the_current_one(self):
		response = self.change(old_password=PASSWORD)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password(self.NEW_PASSWORD))

	def test_requires_the_current_password(self):
		response = self.change()

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("old_password", response.data)

	def test_rejects_a_wrong_current_password(self):
		response = self.change(old_password="not-my-password")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("old_password", response.data)
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password(PASSWORD))


class SetPasswordTests(APITestCase):
	NEW_PASSWORD = "a-different-passphrase"

	def setUp(self):
		self.user = User.objects.create_user(email=EMAIL)
		self.user.set_unusable_password()
		self.user.save()
		self.client.force_authenticate(self.user)

	def test_a_user_without_a_password_sets_one_without_an_old_password(self):
		response = self.client.post(reverse("rest_password_change"), {
			"new_password1": self.NEW_PASSWORD, "new_password2": self.NEW_PASSWORD,
		})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password(self.NEW_PASSWORD))


class SocialAccountTests(APITestCase):

	def setUp(self):
		self.user = User.objects.create_user(email=EMAIL, password=PASSWORD)
		self.google = SocialAccount.objects.create(
			user=self.user, provider="google", uid="1001", extra_data={"email": "ada@gmail.com"},
		)
		self.client.force_authenticate(self.user)

	def disconnect(self, account: SocialAccount):
		return self.client.post(reverse("social_account_disconnect", args=[account.pk]))

	def test_lists_the_callers_connected_accounts_with_their_email(self):
		other = User.objects.create_user(email="grace@example.com")
		SocialAccount.objects.create(user=other, provider="google", uid="2002")

		response = self.client.get(reverse("social_account_list"))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(
			[(row["id"], row["provider"], row["email"]) for row in response.data],
			[(self.google.pk, "google", "ada@gmail.com")],
		)

	def test_an_account_without_an_email_lists_none(self):
		self.google.extra_data = {}
		self.google.save()

		self.assertIsNone(self.client.get(reverse("social_account_list")).data[0]["email"])

	def test_disconnects_google_when_the_user_has_a_password(self):
		response = self.disconnect(self.google)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertFalse(SocialAccount.objects.exists())

	def test_refuses_to_disconnect_the_last_sign_in_method(self):
		self.user.set_unusable_password()
		self.user.save()

		response = self.disconnect(self.google)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("Set a password", response.data["non_field_errors"][0])
		self.assertTrue(SocialAccount.objects.filter(pk=self.google.pk).exists())

	def test_cannot_disconnect_another_users_account(self):
		other = SocialAccount.objects.create(
			user=User.objects.create_user(email="grace@example.com", password=PASSWORD), provider="google", uid="2002",
		)

		self.assertEqual(self.disconnect(other).status_code, status.HTTP_404_NOT_FOUND)
		self.assertTrue(SocialAccount.objects.filter(pk=other.pk).exists())
