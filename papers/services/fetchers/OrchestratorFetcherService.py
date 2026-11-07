import logging
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from xml.etree.ElementTree import ParseError

from requests import RequestException

from papers.services.fetchers.ArxivFetcherService import ArxivFetcherService
from papers.services.fetchers.BaseFetcherService import BaseFetcherService
from papers.services.fetchers.OpenAlexFetcherService import OpenAlexFetcherService
from papers.services.fetchers.SemanticScholarFetcherService import SemanticScholarFetcherService
from papers.services.fetchers.definitions import FetchedPaper

logger = logging.getLogger(__name__)


class OrchestratorFetcherService:
	"""Searches every provider at once and merges their results."""

	FETCHERS: tuple[type[BaseFetcherService], ...] = (
		SemanticScholarFetcherService,
		OpenAlexFetcherService,
		ArxivFetcherService,
	)

	@classmethod
	def search(cls, query: str, limit_per_provider: int = 10, since: date | None = None) -> list[FetchedPaper]:
		"""Returns each provider's papers for `query`, dropping ones an earlier provider already returned."""
		with ThreadPoolExecutor(max_workers=len(cls.FETCHERS)) as executor:
			results = executor.map(
				lambda fetcher: cls.search_provider(fetcher, query, limit_per_provider, since), cls.FETCHERS,
			)
			return cls.deduplicate([paper for papers in results for paper in papers])

	@staticmethod
	def search_provider(
			fetcher: type[BaseFetcherService], query: str, limit: int, since: date | None = None,
	) -> list[FetchedPaper]:
		"""Searches one provider, returning no papers if it fails."""
		try:
			return fetcher.search(query, limit, since)
		except (RequestException, ValueError, ParseError):
			logger.warning("%s search failed for %r", fetcher.source, query, exc_info=True)
			return []

	@staticmethod
	def deduplicate(papers: list[FetchedPaper]) -> list[FetchedPaper]:
		"""Keeps the first paper for each DOI and each title."""
		seen_dois, seen_titles = set(), set()
		unique = []
		for paper in papers:
			doi = paper.doi.lower() if paper.doi else None
			title = "".join(character for character in paper.title.lower() if character.isalnum())
			if doi in seen_dois or title in seen_titles:
				continue
			if doi:
				seen_dois.add(doi)
			seen_titles.add(title)
			unique.append(paper)
		return unique
