from dataclasses import dataclass, field
from datetime import date, datetime

from enums.Paper import DatePrecision, PaperSource


@dataclass
class FetchedAuthor:
	"""An author as a provider returned it, shaped like the Author model."""
	name: str
	orcid: str | None = None


@dataclass
class FetchedPaper:
	"""A paper as a provider returned it, shaped like the Paper model; authors are in byline order."""
	source: PaperSource
	external_id: str
	title: str
	url: str
	doi: str | None = None
	abstract: str | None = None
	venue: str | None = None
	citation_count: int | None = None
	publication_date: date | None = None
	publication_date_precision: DatePrecision | None = None
	pdf_url: str | None = None
	revised_at: datetime | None = None
	authors: list[FetchedAuthor] = field(default_factory=list)
