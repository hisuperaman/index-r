from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from workspaces.models import Workspace
from workspaces.serializers import WorkspaceSerializer
from workspaces.permissions import IsWorkspaceOwner


class UserScopedViewSet(ModelViewSet):
    """
    Mixin to scope queries and creation to the logged-in user.
    Can be reused for any model that has a 'user' foreign key.
    """
    permission_classes = [IsAuthenticated, IsWorkspaceOwner]

    def get_queryset(self):
        # Scopes the view to only the user's objects
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assigns the owner on creation
        serializer.save(user=self.request.user)


class WorkspaceViewSet(UserScopedViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer