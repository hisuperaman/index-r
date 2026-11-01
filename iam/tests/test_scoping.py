from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from iam.models import User
from iam.scoping import scope_to_user
from workspaces.models import TrackedTopic, Workspace


class ScopeToUserTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com")
		other_user = User.objects.create_user(email="grace@example.com")
		cls.workspace = Workspace.objects.create(user=cls.user, name="Mine")
		cls.other_workspace = Workspace.objects.create(user=other_user, name="Theirs")

	def test_keeps_only_the_users_rows(self):
		self.assertQuerySetEqual(scope_to_user(Workspace.objects.all(), self.user), [self.workspace])

	def test_follows_a_relation_to_the_owner(self):
		topic = TrackedTopic.objects.create(workspace=self.workspace, query="sparse retrieval")
		TrackedTopic.objects.create(workspace=self.other_workspace, query="sparse retrieval")

		scoped = scope_to_user(TrackedTopic.objects.all(), self.user, 'workspace__user')

		self.assertQuerySetEqual(scoped, [topic])

	def test_returns_nothing_without_a_logged_in_user(self):
		self.assertQuerySetEqual(scope_to_user(Workspace.objects.all(), None), [])
		self.assertQuerySetEqual(scope_to_user(Workspace.objects.all(), AnonymousUser()), [])
