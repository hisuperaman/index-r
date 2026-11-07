from functools import reduce
from math import log
from operator import or_

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Case, F, FloatField, Prefetch, Q, QuerySet, Value, When
from django.db.models.functions import Cast, Coalesce, ExtractYear, Ln
from django.db.models.lookups import LessThanOrEqual
from django.utils import timezone

from enums.Paper import ChunkLookup


class AuthorQuerySet(QuerySet):

	def find_or_create(self, name: str, orcid: str | None = None):
		"""Returns the author with this ORCID, or else this name, creating one if none exists."""
		if orcid:
			return self.get_or_create(orcid=orcid, defaults={self.model.fields.name: name})[0]
		return self.filter(name=name).first() or self.create(name=name)


class PaperQuerySet(QuerySet):

	def public(self):
		"""Papers in the shared corpus."""
		return self.filter(owner__isnull=True)

	def visible_to(self, user):
		"""The shared corpus plus the papers `user` uploaded."""
		return self.filter(Q(owner__isnull=True) | Q(owner=user.pk))

	def matching(self, source: str, external_id: str, doi: str | None):
		"""Papers with this source ID, or with this DOI."""
		match = Q(source=source, external_id=external_id)
		if doi:
			match |= Q(doi=doi)
		return self.filter(match)

	def with_authors(self):
		"""Papers with their authors loaded in byline order."""
		from papers.models import PaperAuthor

		return self.prefetch_related(Prefetch(
			self.model.fields.paper_authors, queryset=PaperAuthor.objects.select_related(PaperAuthor.fields.author),
		))

	def pending(self):
		"""Papers whose ingestion has neither completed nor failed."""
		return self.filter(ingested_at=None, ingestion_failed_at=None)


class ChunkQuerySet(QuerySet):
	SEARCH_CONFIG = "english"

	def public(self):
		"""Chunks of papers in the shared corpus."""
		return self.filter(paper__owner__isnull=True)

	def visible_to(self, user):
		"""Chunks of the shared corpus and of the papers `user` uploaded."""
		return self.filter(Q(paper__owner__isnull=True) | Q(paper__owner=user.pk))
	CITATION_WEIGHT = 0.1
	RECENCY_YEARS = 5
	RECENCY_BOOST = 0.2

	def search(self, *texts: str):
		"""Chunks matching any of `texts` in web-search syntax, annotated with their `rank` and boosted `score`, best first."""
		if not texts:
			return self.none()
		query = reduce(or_, (SearchQuery(text, config=self.SEARCH_CONFIG, search_type="websearch") for text in texts))
		return (
			self.filter(**{self.model.fields.search_vector: query})
			.annotate(rank=SearchRank(F(self.model.fields.search_vector), query))
			.annotate(score=F(ChunkLookup.rank.value) * self.citation_boost() * self.recency_boost())
			.order_by(ChunkLookup.score.desc(), self.model.fields.id)
		)

	def filter_papers(
			self, year_from: int | None = None, year_to: int | None = None, venue: str | None = None,
			min_citations: int | None = None,
	):
		"""Chunks whose paper was published in the year range, at a matching venue, with enough citations."""
		filters = Q()
		if year_from is not None:
			filters &= Q(paper__publication_date__year__gte=year_from)
		if year_to is not None:
			filters &= Q(paper__publication_date__year__lte=year_to)
		if venue:
			filters &= Q(paper__venue__icontains=venue)
		if min_citations is not None:
			filters &= Q(paper__citation_count__gte=min_citations)
		return self.filter(filters)

	@classmethod
	def citation_boost(cls):
		"""1 + CITATION_WEIGHT × log10(citations + 1)."""
		citations = Cast(Coalesce(ChunkLookup.paper__citation_count.value, 0), FloatField()) + Value(1.0)
		return Value(1.0) + Ln(citations) * Value(cls.CITATION_WEIGHT / log(10))

	@classmethod
	def recency_boost(cls):
		"""Up to 1 + RECENCY_BOOST for this year's papers, falling to 1 at RECENCY_YEARS old and for undated papers."""
		age = Value(timezone.now().year) - ExtractYear(ChunkLookup.paper__publication_date.value)
		return Case(
			When(paper__publication_date__isnull=True, then=Value(1.0)),
			When(LessThanOrEqual(age, Value(0)), then=Value(1.0 + cls.RECENCY_BOOST)),
			When(
				LessThanOrEqual(age, Value(cls.RECENCY_YEARS)),
				then=Value(1.0 + cls.RECENCY_BOOST) - Cast(age, FloatField()) * Value(
					cls.RECENCY_BOOST / cls.RECENCY_YEARS),
			),
			default=Value(1.0),
			output_field=FloatField(),
		)
