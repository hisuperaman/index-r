from django.urls import path

from workspaces.views import PaperCreateView, WorkspaceListCreateView


urlpatterns = [
    path("", WorkspaceListCreateView.as_view(), name="workspace-list-create"),
    path(
        "<uuid:workspace_id>/papers/",
        PaperCreateView.as_view(),
        name="paper-create",
    ),
]