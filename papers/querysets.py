from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, QuerySet


class AuthorQuerySet(QuerySet):

	def find_or_create(self, name: str, orcid: str | None = None):
		"""Returns the author with this ORCID, or else this name, creating one if none exists."""
		if orcid:
			return self.get_or_create(orcid=orcid, defaults={self.model.fields.name: name})[0]
		return self.filter(name=name).first() or self.create(name=name)


class PaperQuerySet(QuerySet):

	def matching(self, source: str, external_id: str, doi: str | None):
		"""Papers with this source ID, or with this DOI."""
		match = Q(source=source, external_id=external_id)
		if doi:
			match |= Q(doi=doi)
		return self.filter(match)

	def pending(self):
		"""Papers whose ingestion has neither completed nor failed."""
		return self.filter(ingested_at=None, ingestion_failed_at=None)


class ChunkQuerySet(QuerySet):
	SEARCH_CONFIG = "english"

	def search(self, text: str):
		"""Chunks matching `text` in web-search syntax, best first, each annotated with its `rank`."""
		query = SearchQuery(text, config=self.SEARCH_CONFIG, search_type="websearch")
		return (
			self.filter(**{self.model.fields.search_vector: query})
			.annotate(rank=SearchRank(F(self.model.fields.search_vector), query))
			.order_by("-rank", self.model.fields.id)
		)
