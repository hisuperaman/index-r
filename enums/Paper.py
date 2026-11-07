from django.db.models import TextChoices

from enums.Enum import FieldEnum


class PaperSource(TextChoices):
	ARXIV = "arxiv", "arXiv"
	SEMANTIC_SCHOLAR = "semantic_scholar", "Semantic Scholar"
	OPENALEX = "openalex", "OpenAlex"
	UPLOAD = "upload", "Upload"


class DatePrecision(TextChoices):
	DAY = "day", "Day"
	MONTH = "month", "Month"
	YEAR = "year", "Year"


class IngestionStatus(TextChoices):
	PENDING = "pending", "Pending"
	COMPLETED = "completed", "Completed"
	FAILED = "failed", "Failed"


class PaperLookup(FieldEnum):
	ingestion_status = 'ingestion_status'
	is_private = 'is_private'
	author_names = 'author_names'
	mention_count = '_mention_count'
	last_mentioned_at = '_last_mentioned_at'
	in_workspace = '_in_workspace'


class ChunkLookup(FieldEnum):
	paper__citation_count = 'paper__citation_count'
	paper__publication_date = 'paper__publication_date'
	citation = 'citation'
	rank = 'rank'
	score = 'score'
