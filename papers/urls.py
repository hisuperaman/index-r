from django.urls import path

from papers.views import ChunkSearchView

urlpatterns = [
	path('chunks/search/', ChunkSearchView.as_view(), name='chunk-search'),
]
