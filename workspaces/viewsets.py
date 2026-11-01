from rest_framework import permissions, viewsets

from .models import Workspace
from .permissions import OWNER_FIELD, IsWorkspaceOwner
from .serializers import WorkspaceSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):

    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceOwner]

    def get_queryset(self):
        # Other users' workspaces do not exist for this user (404, no leak).
        return Workspace.objects.filter(**{OWNER_FIELD: self.request.user})

    def perform_create(self, serializer):
        serializer.save(**{OWNER_FIELD: self.request.user})
