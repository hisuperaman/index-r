from django.test import TestCase
from rest_framework.test import APIRequestFactory

from iam.models import User
from iam.permissions import IsOwner
from workspaces.models import TrackedTopic, Workspace


class IsWorkspaceOwner(IsOwner):
	owner_field = 'workspace.user_id'


def has_object_permission(permission: IsOwner, user, obj) -> bool:
	request = APIRequestFactory().get("/")
	request.user = user
	return permission.has_object_permission(request, None, obj)


class IsOwnerTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.owner = User.objects.create_user(email="ada@example.com")
		cls.other_user = User.objects.create_user(email="grace@example.com")
		cls.workspace = Workspace.objects.create(user=cls.owner, name="Retrieval")
		cls.topic = TrackedTopic.objects.create(workspace=cls.workspace, query="sparse retrieval")

	def test_allows_the_owner(self):
		self.assertTrue(has_object_permission(IsOwner(), self.owner, self.workspace))

	def test_denies_another_user(self):
		self.assertFalse(has_object_permission(IsOwner(), self.other_user, self.workspace))

	def test_denies_a_superuser_who_is_not_the_owner(self):
		superuser = User.objects.create_superuser(email="admin@example.com")

		self.assertFalse(has_object_permission(IsOwner(), superuser, self.workspace))

	def test_follows_owner_field_through_a_relation(self):
		self.assertTrue(has_object_permission(IsWorkspaceOwner(), self.owner, self.topic))
		self.assertFalse(has_object_permission(IsWorkspaceOwner(), self.other_user, self.topic))
