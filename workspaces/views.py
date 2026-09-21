from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from workspaces.models import Paper, Workspace
from workspaces.serializers import PaperSerializer, WorkspaceSerializer


class WorkspaceListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Workspace.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaperCreateView(generics.CreateAPIView):
    serializer_class = PaperSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        workspace = get_object_or_404(
            Workspace,
            id=self.kwargs["workspace_id"],
            user=self.request.user,
        )

        serializer.save(workspace=workspace)