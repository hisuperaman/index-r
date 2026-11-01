from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from enums.Workspace import MessageRole
from iam.mixins import UserScopedMixin
from iam.permissions import IsOwner
from workspaces.mixins import WorkspaceScopedMixin
from workspaces.models import Message, Workspace, WorkspacePaper
from workspaces.serializers import MessageSerializer, WorkspacePaperSerializer, WorkspaceSerializer


class WorkspaceViewSet(UserScopedMixin, ModelViewSet):
	"""Creates, lists, renames and deletes the caller's own workspaces."""
	queryset = Workspace.objects.all()
	serializer_class = WorkspaceSerializer
	permission_classes = [IsOwner]
	ordering_fields = [Workspace.fields.name, Workspace.fields.created_at, Workspace.fields.updated_at]
	ordering = [Workspace.fields.created_at.desc()]


class WorkspacePaperViewSet(WorkspaceScopedMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
	"""Lists, adds and removes the papers in one of the caller's workspaces."""
	queryset = WorkspacePaper.objects.select_related(WorkspacePaper.fields.paper)
	serializer_class = WorkspacePaperSerializer
	lookup_field = WorkspacePaper.fields.paper
	ordering_fields = [WorkspacePaper.fields.created_at]
	ordering = [WorkspacePaper.fields.created_at.desc()]

	def get_serializer(self, *args, **kwargs):
		return super().get_serializer(*args, workspace=self.workspace, **kwargs)


class MessageViewSet(WorkspaceScopedMixin, ListModelMixin, CreateModelMixin, GenericViewSet):
	"""Lists the chat in one of the caller's workspaces, newest first, and posts the caller's messages to it."""
	queryset = Message.objects.all()
	serializer_class = MessageSerializer
	ordering_fields = [Message.fields.created_at]
	ordering = [Message.fields.created_at.desc()]

	def perform_create(self, serializer):
		serializer.save(workspace=self.workspace, role=MessageRole.USER)
