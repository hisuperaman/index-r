from rest_framework.generics import ListAPIView

from papers.models import Chunk
from papers.serializers import ChunkSerializer


class ChunkSearchView(ListAPIView):
	"""Lists the chunks that best match the `q` query parameter."""
	serializer_class = ChunkSerializer
	filter_backends = []
	pagination_class = None
	limit = 50

	def get_queryset(self):
		serializer = self.get_serializer(data=self.request.query_params)
		serializer.is_valid(raise_exception=True)
		return Chunk.objects.search(serializer.validated_data['q']).select_related(Chunk.fields.paper)[:self.limit]
