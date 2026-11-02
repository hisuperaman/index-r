from django.urls import include, path
from rest_framework.routers import SimpleRouter

from integrations.views import ApiTokenViewSet, McpServerView

router = SimpleRouter()
router.register('tokens', ApiTokenViewSet, basename='api-token')

urlpatterns = [
	path('mcp/', McpServerView.as_view(), name='mcp-server'),
	path('', include(router.urls)),
]
