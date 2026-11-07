from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from iam.models import User
from server.permissions import BasePermission


class DeniesEverything(BasePermission):
	public_methods = ['GET']

	def check_permissions(self, request, view) -> bool:
		return False

	def check_object_permissions(self, request, view, obj) -> bool:
		return False


def has_permission(permission: BasePermission, user, method: str = 'post', obj=None) -> bool:
	request = getattr(APIRequestFactory(), method)("/")
	request.user = user
	if obj is None:
		return permission.has_permission(request, None)
	return permission.has_object_permission(request, None, obj)


class BasePermissionTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com")
		cls.superuser = User.objects.create_superuser(email="admin@example.com")

	def test_allows_a_logged_in_user(self):
		self.assertTrue(has_permission(BasePermission(), self.user))

	def test_denies_an_anonymous_user(self):
		self.assertFalse(has_permission(BasePermission(), AnonymousUser()))

	def test_a_public_method_skips_every_check(self):
		self.assertTrue(has_permission(DeniesEverything(), AnonymousUser(), method='get'))

	def test_runs_the_request_check_for_a_regular_user(self):
		self.assertFalse(has_permission(DeniesEverything(), self.user))

	def test_runs_the_object_check_for_a_regular_user(self):
		self.assertFalse(has_permission(DeniesEverything(), self.user, obj=self.user))

	def test_a_superuser_gets_the_same_checks(self):
		self.assertFalse(has_permission(DeniesEverything(), self.superuser))
		self.assertFalse(has_permission(DeniesEverything(), self.superuser, obj=self.user))

