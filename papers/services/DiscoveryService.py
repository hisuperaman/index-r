from django.conf import settings

from papers.models import Paper
from papers.services.PaperStoreService import PaperStoreService
from papers.services.QueryExpansionService import QueryExpansionService
from papers.services.RerankService import RerankService
from papers.services.fetchers import OrchestratorFetcherService
from papers.services.fetchers.definitions import FetchedPaper


class DiscoveryService:
	"""Finds papers on a question in the external sources and adds the relevant ones to the corpus."""

	LIMIT_PER_PROVIDER = 10

	@classmethod
	def discover(cls, question: str, queries: list[str] | None = None) -> list[Paper]:
		"""Fetches papers for the question's queries, keeps those with a relevant abstract and stores them."""
		queries = queries or QueryExpansionService.expand(question)
		return PaperStoreService.store(cls.filter_relevant(question, cls.fetch(queries)))

	@classmethod
	def fetch(cls, queries: list[str]) -> list[FetchedPaper]:
		"""Searches every provider for every query, merging the results without duplicates."""
		papers = [
			paper
			for query in queries
			for paper in OrchestratorFetcherService.search(query, cls.LIMIT_PER_PROVIDER)
		]
		return OrchestratorFetcherService.deduplicate(papers)

	@staticmethod
	def filter_relevant(question: str, papers: list[FetchedPaper]) -> list[FetchedPaper]:
		"""Keeps the papers whose title and abstract score at least DISCOVERY_ABSTRACT_MIN_SCORE, best first."""
		documents = [f"{paper.title}\n{paper.abstract or ''}".strip() for paper in papers]
		return [
			papers[index]
			for index, score in RerankService.score(question, documents)
			if score >= settings.DISCOVERY_ABSTRACT_MIN_SCORE
		]
