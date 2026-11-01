from rest_framework.viewsets import ModelViewSet

from iam.mixins import UserScopedMixin
from iam.permissions import IsOwner
from workspaces.models import Workspace
from workspaces.serializers import WorkspaceSerializer


class WorkspaceViewSet(UserScopedMixin, ModelViewSet):
	"""Creates, lists, renames and deletes the caller's own workspaces."""
	queryset = Workspace.objects.all()
	serializer_class = WorkspaceSerializer
	permission_classes = [IsOwner]
	ordering_fields = [Workspace.fields.name, Workspace.fields.created_at, Workspace.fields.updated_at]
	ordering = [Workspace.fields.created_at.desc()]
