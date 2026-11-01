from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from iam.adapters import CustomSocialAccountAdapter
from iam.models import User


class ConnectGoogleTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.me = User.objects.create_user(email="ada@example.com", password="password")
		cls.other = User.objects.create_user(email="grace@example.com", password="password")

	def connect(self, account: SocialAccount, user: User):
		request = APIRequestFactory().post("/")
		request.user = self.me
		login = SocialLogin(user=user, account=account)
		login.state["process"] = "connect"
		CustomSocialAccountAdapter(request).pre_social_login(request, login)

	def test_rejects_a_google_account_linked_to_another_user(self):
		account = SocialAccount.objects.create(user=self.other, provider="google", uid="2002")

		with self.assertRaisesMessage(ValidationError, "already connected to another IndexR account"):
			self.connect(account, self.other)

	def test_allows_the_users_own_google_account(self):
		account = SocialAccount.objects.create(user=self.me, provider="google", uid="1001")

		self.connect(account, self.me)

	def test_does_not_attach_a_new_google_account_to_another_user_with_its_email(self):
		account = SocialAccount(provider="google", uid="3003")
		new_user = User(email=self.other.email)

		self.connect(account, new_user)

		self.assertFalse(SocialAccount.objects.filter(user=self.other).exists())
