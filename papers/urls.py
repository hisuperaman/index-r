from django.urls import include, path
from rest_framework.routers import SimpleRouter

from papers.views import ChunkSearchView, PaperViewSet

router = SimpleRouter()
router.register('', PaperViewSet, basename='paper')

urlpatterns = [
	path('chunks/search/', ChunkSearchView.as_view(), name='chunk-search'),
	path('', include(router.urls)),
]
