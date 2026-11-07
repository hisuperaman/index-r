from django.urls import include, path
from rest_framework.routers import SimpleRouter

from workspaces.views import (
	MentionedPaperViewSet, MessageViewSet, TrackedTopicViewSet, TrackingUpdateViewSet, WorkspacePaperViewSet,
	WorkspaceViewSet,
)

router = SimpleRouter()
router.register(r'(?P<workspace_pk>[^/.]+)/papers', WorkspacePaperViewSet, basename='workspace-paper')
router.register(r'(?P<workspace_pk>[^/.]+)/messages', MessageViewSet, basename='workspace-message')
router.register(
	r'(?P<workspace_pk>[^/.]+)/mentioned-papers', MentionedPaperViewSet, basename='workspace-mentioned-paper',
)
router.register(r'(?P<workspace_pk>[^/.]+)/topics', TrackedTopicViewSet, basename='workspace-topic')
router.register(r'(?P<workspace_pk>[^/.]+)/updates', TrackingUpdateViewSet, basename='workspace-update')
router.register('', WorkspaceViewSet, basename='workspace')

urlpatterns = [
	path('', include(router.urls)),
]
