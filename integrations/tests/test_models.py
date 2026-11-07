from django.db import IntegrityError
from django.test import TestCase

from iam.models import User
from integrations.models import ApiToken


class ApiTokenTests(TestCase):

	def test_name_cannot_be_blank(self):
		user = User.objects.create_user(email="ada@example.com", password="password")

		with self.assertRaises(IntegrityError):
			ApiToken.objects.issue(user, "")
