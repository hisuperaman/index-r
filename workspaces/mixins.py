from functools import cached_property

from rest_framework.generics import get_object_or_404

from iam.scoping import scope_to_user
from workspaces.models import Workspace


class WorkspaceScopedMixin:
	"""Nests a view under the caller's workspace named by the `workspace_pk` URL kwarg, or 404s."""

	@cached_property
	def workspace(self) -> Workspace:
		return get_object_or_404(scope_to_user(Workspace.objects.all(), self.request.user),
								 pk=self.kwargs['workspace_pk'])

	def get_queryset(self):
		return super().get_queryset().filter(workspace=self.workspace)

	def perform_create(self, serializer):
		serializer.save(workspace=self.workspace)
