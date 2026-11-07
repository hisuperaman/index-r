from django.db.models import Model
from rest_framework.permissions import BasePermission as _
from rest_framework.request import Request
from rest_framework.views import APIView


class BasePermission(_):
	"""Requires login and leaves the rest to check_permissions and check_object_permissions."""
	public_methods: list[str] = []

	def has_permission(self, request: Request, view: APIView) -> bool:
		return self.has_object_permission(request, view, None)

	def has_object_permission(self, request: Request, view: APIView, obj: Model | None) -> bool:
		if request.method in self.public_methods:
			return True
		if not request.user.is_authenticated:
			return False
		if obj is None:
			return self.check_permissions(request, view)
		return self.check_object_permissions(request, view, obj)

	def check_permissions(self, request: Request, view: APIView) -> bool:
		return True

	def check_object_permissions(self, request: Request, view: APIView, obj: Model) -> bool:
		return True
