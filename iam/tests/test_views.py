from allauth.account.models import EmailAddress
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
