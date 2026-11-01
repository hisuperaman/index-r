from django.urls import include, path
from rest_framework.routers import SimpleRouter

from workspaces.views import WorkspaceViewSet

router = SimpleRouter()
router.register('', WorkspaceViewSet, basename='workspace')

urlpatterns = [
	path('', include(router.urls)),
]
