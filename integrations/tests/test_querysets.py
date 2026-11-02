from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from iam.models import User
from integrations.models import ApiToken
from integrations.querysets import TOKEN_PREFIX, hash_token


class ApiTokenQuerySetTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")

	def test_issues_a_token_storing_only_its_hash(self):
		token = ApiToken.objects.issue(self.user, "Claude Desktop")

		self.assertTrue(token.raw_token.startswith(TOKEN_PREFIX))
		stored = ApiToken.objects.get(pk=token.pk)
		self.assertEqual(stored.key_hash, hash_token(token.raw_token))
		self.assertTrue(token.raw_token.startswith(stored.prefix))
		self.assertNotIn(token.raw_token, (stored.key_hash, stored.prefix))

	def test_authenticates_a_valid_token_and_notes_its_use(self):
		token = ApiToken.objects.issue(self.user, "Claude Desktop")

		found = ApiToken.objects.authenticate(token.raw_token)

		self.assertEqual((found, found.user), (token, self.user))
		self.assertIsNotNone(ApiToken.objects.get(pk=token.pk).last_used_at)

	def test_does_not_rewrite_a_recent_last_use(self):
		token = ApiToken.objects.issue(self.user, "Claude Desktop")
		recent = timezone.now() - timedelta(minutes=1)
		ApiToken.objects.filter(pk=token.pk).update(last_used_at=recent)

		ApiToken.objects.authenticate(token.raw_token)

		self.assertEqual(ApiToken.objects.get(pk=token.pk).last_used_at, recent)

	def test_rejects_unknown_malformed_and_empty_tokens(self):
		ApiToken.objects.issue(self.user, "Claude Desktop")

		for raw in (f"{TOKEN_PREFIX}not-a-real-token", "abc", "", None):
			self.assertIsNone(ApiToken.objects.authenticate(raw))

	def test_rejects_a_deactivated_users_token(self):
		token = ApiToken.objects.issue(self.user, "Claude Desktop")
		User.objects.filter(pk=self.user.pk).update(is_active=False)

		self.assertIsNone(ApiToken.objects.authenticate(token.raw_token))
