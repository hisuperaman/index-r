from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from papers.models import Chunk, Paper
from papers.serializers import ChunkSerializer, PaperSerializer
from server.filters import OrderingFilter


class ChunkSearchView(ListAPIView):
	"""Lists the chunks that best match the `q` query parameter, within the optional paper filters."""
	serializer_class = ChunkSerializer
	filter_backends = []
	pagination_class = None
	limit = 50

	def get_queryset(self):
		serializer = self.get_serializer(data=self.request.query_params)
		serializer.is_valid(raise_exception=True)
		filters = serializer.validated_data
		return (
			Chunk.objects
			.filter_papers(
				year_from=filters.get('year_from'), year_to=filters.get('year_to'), venue=filters.get('venue'),
				min_citations=filters.get('min_citations'),
			)
			.search(filters['q'])
			.select_related(Chunk.fields.paper)[:self.limit]
		)


class PaperViewSet(ReadOnlyModelViewSet):
	"""Browses the shared corpus, newest first, searchable by title or DOI."""
	queryset = Paper.objects.with_authors()
	serializer_class = PaperSerializer
	filter_backends = [SearchFilter, OrderingFilter]
	search_fields = [Paper.fields.title, Paper.fields.doi]
	ordering_fields = [Paper.fields.created_at, Paper.fields.citation_count, Paper.fields.publication_date]
	ordering = [Paper.fields.created_at.desc()]
	lookup_value_regex = '[0-9a-f-]{36}'
