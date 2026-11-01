from operator import attrgetter

from django.db.models import Model
from rest_framework.request import Request
from rest_framework.views import APIView

from server.permissions import BasePermission


class IsOwner(BasePermission):
	"""Allows a detail route only on an object whose `owner_field` is the caller's id."""
	owner_field = 'user_id'

	def check_object_permissions(self, request: Request, view: APIView, obj: Model) -> bool:
		return attrgetter(self.owner_field)(obj) == request.user.pk
