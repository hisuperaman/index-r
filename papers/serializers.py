from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer

from papers.models import Chunk, Paper


class PaperBasicSerializer(ModelSerializer):
	class Meta:
		model = Paper
		fields = [
			Paper.fields.id, Paper.fields.title, Paper.fields.doi, Paper.fields.venue, Paper.fields.citation_count,
			Paper.fields.publication_date, Paper.fields.publication_date_precision, Paper.fields.url,
			Paper.fields.pdf_url,
		]
		read_only_fields = fields


class PaperSerializer(PaperBasicSerializer):
	authors = ListField(child=CharField(), source='author_names', read_only=True)

	class Meta(PaperBasicSerializer.Meta):
		fields = [*PaperBasicSerializer.Meta.fields, 'authors']
		read_only_fields = fields


class ChunkSerializer(ModelSerializer):
	paper = PaperBasicSerializer(read_only=True)
	citation = CharField(read_only=True)
	rank = FloatField(read_only=True)
	score = FloatField(read_only=True)
	q = CharField(write_only=True, max_length=500)
	year_from = IntegerField(write_only=True, required=False, min_value=1, max_value=9999)
	year_to = IntegerField(write_only=True, required=False, min_value=1, max_value=9999)
	venue = CharField(write_only=True, required=False, max_length=500)
	min_citations = IntegerField(write_only=True, required=False, min_value=0)

	class Meta:
		model = Chunk
		read_only_fields = [
			Chunk.fields.id, Chunk.fields.paper, Chunk.fields.heading, Chunk.fields.text, Chunk.fields.start_page,
			Chunk.fields.end_page, Chunk.fields.chunk_index, 'citation', 'rank', 'score',
		]
		fields = [*read_only_fields, 'q', 'year_from', 'year_to', 'venue', 'min_citations']

	def validate(self, data):
		data = super().validate(data)
		year_from, year_to = data.get('year_from'), data.get('year_to')
		if year_from is not None and year_to is not None and year_from > year_to:
			raise ValidationError({'year_to': ["Must not be before year_from."]})
		return data
