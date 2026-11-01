from django.urls import include, path
from rest_framework.routers import SimpleRouter

from workspaces.views import MentionedPaperViewSet, MessageViewSet, WorkspacePaperViewSet, WorkspaceViewSet

router = SimpleRouter()
router.register(r'(?P<workspace_pk>[^/.]+)/papers', WorkspacePaperViewSet, basename='workspace-paper')
router.register(r'(?P<workspace_pk>[^/.]+)/messages', MessageViewSet, basename='workspace-message')
router.register(
	r'(?P<workspace_pk>[^/.]+)/mentioned-papers', MentionedPaperViewSet, basename='workspace-mentioned-paper',
)
router.register('', WorkspaceViewSet, basename='workspace')

urlpatterns = [
	path('', include(router.urls)),
]
