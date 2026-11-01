from rest_framework.fields import CharField, FloatField
from rest_framework.serializers import ModelSerializer

from papers.models import Chunk, Paper


class PaperSerializer(ModelSerializer):
	class Meta:
		model = Paper
		fields = [
			Paper.fields.id, Paper.fields.title, Paper.fields.doi, Paper.fields.venue, Paper.fields.citation_count,
			Paper.fields.publication_date, Paper.fields.publication_date_precision, Paper.fields.url,
			Paper.fields.pdf_url,
		]
		read_only_fields = fields


class ChunkSerializer(ModelSerializer):
	paper = PaperSerializer(read_only=True)
	rank = FloatField(read_only=True)
	q = CharField(write_only=True, max_length=500)

	class Meta:
		model = Chunk
		read_only_fields = [
			Chunk.fields.id, Chunk.fields.paper, Chunk.fields.heading, Chunk.fields.text, Chunk.fields.start_page,
			Chunk.fields.end_page, Chunk.fields.chunk_index, 'rank',
		]
		fields = [*read_only_fields, 'q']
