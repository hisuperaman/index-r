from django.conf import settings
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from iam.mixins import UserScopedMixin
from iam.permissions import IsOwner
from integrations.models import ApiToken
from integrations.serializers import ApiTokenSerializer


class ApiTokenViewSet(UserScopedMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
	"""Lists, creates and revokes the caller's personal access tokens."""
	queryset = ApiToken.objects.all()
	serializer_class = ApiTokenSerializer
	permission_classes = [IsOwner]
	pagination_class = None
	ordering = [ApiToken.fields.created_at.desc()]


class McpServerView(APIView):
	"""Tells the caller where the MCP server is."""

	def get(self, request):
		return Response({'url': settings.MCP_PUBLIC_URL})
