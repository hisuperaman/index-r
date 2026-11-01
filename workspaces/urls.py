from rest_framework.routers import DefaultRouter

from .viewsets import WorkspaceViewSet

router = DefaultRouter()
router.register("workspaces", WorkspaceViewSet, basename="workspace")
urlpatterns = router.urls
