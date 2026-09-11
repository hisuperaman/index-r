from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db.models import (
	CharField, TextField, DateField,
	ForeignKey, ManyToManyField, PositiveIntegerField,
	Index, Q, F, CheckConstraint, UniqueConstraint, CASCADE, URLField,
)

from enums.Paper import PaperSource, DatePrecision, IngestionStatus
from server.models import BaseModel, PrimaryModel


class Author(BaseModel):
	name = CharField(max_length=255)
	orcid = CharField(max_length=19, blank=True, null=True, unique=True)

	class Meta:
		indexes = [
			Index(fields=["name"]),
		]

	def __str__(self):
		return self.name


class Paper(PrimaryModel):
	source = CharField(max_length=50, choices=PaperSource)
	external_id = CharField(max_length=255)
	doi = CharField(max_length=255, blank=True, null=True, unique=True)  # Digital Object Identifier
	title = TextField()
	abstract = TextField(blank=True, null=True)
	venue = CharField(max_length=500, blank=True, null=True)
	citation_count = PositiveIntegerField(blank=True, null=True)
	publication_date = DateField(blank=True, null=True)
	publication_date_precision = CharField(
		max_length=5,
		choices=DatePrecision,
		blank=True, null=True,
	)
	url = URLField(max_length=1000)
	pdf_url = URLField(max_length=1000, blank=True, null=True)
	authors = ManyToManyField(
		Author,
		through="PaperAuthor",
		related_name="papers",
	)
	ingestion_status = CharField(
		max_length=20,
		choices=IngestionStatus,
		default=IngestionStatus.PENDING,
	)

	class Meta:
		constraints = [
			UniqueConstraint(
				fields=["source", "external_id"],
				name="unique_source_external_id",
			),
			CheckConstraint(
				condition=(
						Q(publication_date__isnull=True, publication_date_precision__isnull=True) |
						Q(publication_date__isnull=False, publication_date_precision__isnull=False)
				),
				name="paper_pub_date_and_precision_consistent",
			),
			CheckConstraint(
				condition=(
						Q(publication_date__isnull=True)
						| Q(publication_date_precision="day")
						| Q(publication_date_precision="month", publication_date__day=1)
						| Q(publication_date_precision="year",
							publication_date__day=1,
							publication_date__month=1)
				),
				name="paper_pub_date_precision_implies_default_values",
			),
		]
		indexes = [
			Index(fields=["-publication_date"]),
			Index(fields=["-citation_count"]),
			Index(fields=["ingestion_status"]),
		]

	def __str__(self):
		return f"[{self.source}] {self.title[:50]}"


class PaperAuthor(BaseModel):
	paper = ForeignKey(Paper, on_delete=CASCADE, related_name="paper_authors")
	author = ForeignKey(Author, on_delete=CASCADE, related_name="paper_authors")
	order = PositiveIntegerField()

	class Meta:
		ordering = ["order"]
		constraints = [
			UniqueConstraint(fields=["paper", "author"], name="unique_paper_author"),
			UniqueConstraint(fields=["paper", "order"], name="unique_paper_author_order"),
		]

	def __str__(self):
		return f"{self.author.name} (#{self.order}) on {self.paper.title[:30]}"


class Chunk(BaseModel):
	paper = ForeignKey(Paper, on_delete=CASCADE, related_name="chunks")
	heading = CharField(max_length=500, blank=True, null=True)
	text = TextField()
	search_vector = SearchVectorField(null=True, blank=True)
	start_page = PositiveIntegerField()
	end_page = PositiveIntegerField()
	chunk_index = PositiveIntegerField()

	class Meta:
		constraints = [
			UniqueConstraint(fields=["paper", "chunk_index"], name="unique_paper_chunk_index"),
			CheckConstraint(condition=Q(end_page__gte=F("start_page")), name="chunk_end_page_gte_start_page"),
			CheckConstraint(condition=Q(start_page__gte=1), name="chunk_start_page_positive"),
		]
		indexes = [
			Index(fields=["paper", "chunk_index"]),
			GinIndex(fields=["search_vector"], name="chunk_search_vector_gin"),
		]

	def __str__(self):
		if self.start_page == self.end_page:
			return f"Chunk {self.chunk_index} (p.{self.start_page})"
		return f"Chunk {self.chunk_index} (pp.{self.start_page}–{self.end_page})"
