from django.db.models import TextChoices


class PaperSource(TextChoices):
	ARXIV = "arxiv", "arXiv"
	SEMANTIC_SCHOLAR = "semantic_scholar", "Semantic Scholar"
	OPENALEX = "openalex", "OpenAlex"


class DatePrecision(TextChoices):
	DAY = "day", "Day"
	MONTH = "month", "Month"
	YEAR = "year", "Year"


class IngestionStatus(TextChoices):
	PENDING = "pending", "Pending"
	COMPLETED = "completed", "Completed"
	FAILED = "failed", "Failed"
