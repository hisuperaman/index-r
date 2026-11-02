from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, FileField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer

from enums.Paper import ChunkLookup, PaperLookup
from papers.exceptions import PaperUploadError
from papers.models import Chunk, Paper
from papers.services.PaperUploadService import PaperUploadService
from papers.services.PdfDownloadService import PdfDownloadService


class PaperBasicSerializer(ModelSerializer):
	is_private = BooleanField(read_only=True)

	class Meta:
		model = Paper
		fields = [
			Paper.fields.id, Paper.fields.title, Paper.fields.doi, Paper.fields.venue, Paper.fields.citation_count,
			Paper.fields.publication_date, Paper.fields.publication_date_precision, Paper.fields.url,
			Paper.fields.pdf_url, Paper.fields.revised_at, PaperLookup.is_private.value,
		]
		read_only_fields = fields


class PaperSerializer(PaperBasicSerializer):
	authors = ListField(child=CharField(), source=PaperLookup.author_names.value, read_only=True)
	title = CharField(required=False, allow_blank=True, max_length=500)
	file = FileField(write_only=True)

	class Meta(PaperBasicSerializer.Meta):
		read_only_fields = [field for field in PaperBasicSerializer.Meta.fields if field != Paper.fields.title]
		fields = [*PaperBasicSerializer.Meta.fields, 'authors', 'file']

	def validate_file(self, file):
		if file.size > PdfDownloadService.MAX_BYTES:
			raise ValidationError(f"Upload a PDF smaller than {PdfDownloadService.MAX_BYTES // (1024 * 1024)} MB.")
		header = file.read(len(PdfDownloadService.PDF_SIGNATURE))
		file.seek(0)
		if header != PdfDownloadService.PDF_SIGNATURE:
			raise ValidationError("Upload a PDF file.")
		return file

	def create(self, validated_data):
		try:
			return PaperUploadService.upload(
				validated_data[Paper.fields.owner], validated_data['file'], validated_data.get(Paper.fields.title, ""),
			)
		except PaperUploadError as error:
			raise ValidationError({'file': [str(error)]}) from error


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
			Chunk.fields.end_page, Chunk.fields.chunk_index, ChunkLookup.citation.value, ChunkLookup.rank.value,
			ChunkLookup.score.value,
		]
		fields = [*read_only_fields, 'q', 'year_from', 'year_to', 'venue', 'min_citations']

	def validate(self, data):
		data = super().validate(data)
		year_from, year_to = data.get('year_from'), data.get('year_to')
		if year_from is not None and year_to is not None and year_from > year_to:
			raise ValidationError({'year_to': ["Must not be before year_from."]})
		return data
