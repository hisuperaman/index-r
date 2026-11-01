from rest_framework.generics import ListAPIView

from papers.models import Chunk
from papers.serializers import ChunkSerializer


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
