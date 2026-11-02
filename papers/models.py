from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import transaction
from django.contrib.postgres.search import SearchVectorField
from django.db.models import (
	CharField, TextField, DateField, DateTimeField,
	ForeignKey, ManyToManyField, PositiveIntegerField,
	Index, Q, F, CheckConstraint, UniqueConstraint, CASCADE, URLField,
)

from enums.Paper import PaperSource, DatePrecision, IngestionStatus
from papers.definitions import ExtractedChunk
from papers.querysets import AuthorQuerySet, ChunkQuerySet, PaperQuerySet
from server.models import BaseModel, PrimaryModel


class Author(BaseModel):
	name = CharField(max_length=255)
	orcid = CharField(max_length=19, blank=True, null=True, unique=True)

	objects = AuthorQuerySet.as_manager()

	class Meta:
		indexes = [
			Index(fields=["name"]),
		]

	def __str__(self):
		return self.name


class Paper(PrimaryModel):
	source = CharField(max_length=50, choices=PaperSource)
	external_id = CharField(max_length=255)
	doi = CharField(max_length=255, blank=True, null=True)  # Digital Object Identifier
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
	url = URLField(max_length=1000, blank=True)
	pdf_url = URLField(max_length=1000, blank=True, null=True)
	authors = ManyToManyField(
		Author,
		through="PaperAuthor",
		related_name="papers",
	)
	owner = ForeignKey(
		settings.AUTH_USER_MODEL, on_delete=CASCADE, blank=True, null=True, related_name="uploaded_papers",
	)
	content_hash = CharField(max_length=64, blank=True, null=True)
	ingested_at = DateTimeField(blank=True, null=True)
	ingestion_failed_at = DateTimeField(blank=True, null=True)
	references = ManyToManyField(
		"self",
		through="Citation",
		through_fields=("citing_paper", "cited_paper"),
		symmetrical=False,
		related_name="cited_by",
	)

	objects = PaperQuerySet.as_manager()

	class Meta:
		constraints = [
			UniqueConstraint(
				fields=["source", "external_id"],
				name="unique_source_external_id",
			),
			UniqueConstraint(fields=["doi"], condition=Q(owner__isnull=True), name="unique_public_paper_doi"),
			UniqueConstraint(fields=["owner", "content_hash"], name="unique_upload_per_owner"),
			CheckConstraint(
				condition=(
						Q(owner__isnull=True) & ~Q(source=PaperSource.UPLOAD)
						| Q(owner__isnull=False, source=PaperSource.UPLOAD)
				),
				name="paper_uploads_are_private",
			),
			CheckConstraint(
				condition=(
						Q(publication_date__isnull=True, publication_date_precision__isnull=True) |
						Q(publication_date__isnull=False, publication_date_precision__isnull=False)
				),
				name="paper_pub_date_and_precision_consistent",
			),
			CheckConstraint(
				condition=Q(ingested_at__isnull=True) | Q(ingestion_failed_at__isnull=True),
				name="paper_ingested_or_failed_not_both",
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
		]

	def __str__(self):
		return f"[{self.source}] {self.title[:50]}"

	@transaction.atomic
	def replace_chunks(self, chunks: list[ExtractedChunk]) -> list["Chunk"]:
		"""Replaces the paper's chunks with `chunks`."""
		self.chunks.all().delete()
		return Chunk.objects.bulk_create(
			Chunk(
				paper=self,
				heading=chunk.heading,
				text=chunk.text,
				start_page=chunk.start_page,
				end_page=chunk.end_page,
				chunk_index=chunk.chunk_index,
			)
			for chunk in chunks
		)

	@property
	def is_private(self) -> bool:
		return self.owner_id is not None

	@property
	def author_names(self) -> list[str]:
		"""The authors' names in byline order."""
		return [paper_author.author.name for paper_author in self.paper_authors.all()]

	@property
	def ingestion_status(self) -> IngestionStatus:
		if self.ingested_at:
			return IngestionStatus.COMPLETED
		if self.ingestion_failed_at:
			return IngestionStatus.FAILED
		return IngestionStatus.PENDING


class Citation(BaseModel):
	"""An edge from a paper to one paper in its reference list."""
	citing_paper = ForeignKey(Paper, on_delete=CASCADE, related_name="outgoing_citations")
	cited_paper = ForeignKey(Paper, on_delete=CASCADE, related_name="incoming_citations")

	class Meta:
		constraints = [
			UniqueConstraint(fields=["citing_paper", "cited_paper"], name="unique_citation"),
			CheckConstraint(condition=~Q(citing_paper=F("cited_paper")), name="citation_not_self"),
		]

	def __str__(self):
		return f"{self.citing_paper_id} cites {self.cited_paper_id}"


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

	objects = ChunkQuerySet.as_manager()

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
		return f"Chunk {self.chunk_index} ({self.pages})"

	@property
	def pages(self) -> str:
		if self.start_page == self.end_page:
			return f"p.{self.start_page}"
		return f"pp.{self.start_page}–{self.end_page}"

	@property
	def citation(self) -> str:
		"""The chunk as `Paper title, §Section, p.X`, leaving out the section when it has no heading."""
		section = f", §{self.heading}" if self.heading else ""
		return f"{self.paper.title}{section}, {self.pages}"
