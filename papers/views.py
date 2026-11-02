from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
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
			Chunk.objects.visible_to(self.request.user)
			.filter_papers(
				year_from=filters.get('year_from'), year_to=filters.get('year_to'), venue=filters.get('venue'),
				min_citations=filters.get('min_citations'),
			)
			.search(filters['q'])
			.select_related(Chunk.fields.paper)[:self.limit]
		)


class PaperViewSet(CreateModelMixin, ReadOnlyModelViewSet):
	"""Browses the papers the caller can see, newest first, and uploads private papers."""
	serializer_class = PaperSerializer
	parser_classes = [MultiPartParser, FormParser, JSONParser]
	filter_backends = [SearchFilter, OrderingFilter]
	search_fields = [Paper.fields.title, Paper.fields.doi]
	ordering_fields = [Paper.fields.created_at, Paper.fields.citation_count, Paper.fields.publication_date]
	ordering = [Paper.fields.created_at.desc()]
	lookup_value_regex = '[0-9a-f-]{36}'

	def get_queryset(self):
		return Paper.objects.visible_to(self.request.user).with_authors()

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)
