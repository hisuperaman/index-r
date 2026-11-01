from dataclasses import dataclass

from django.conf import settings

from papers.models import Chunk
from papers.services.RerankService import RerankService


@dataclass
class Retrieval:
	"""The passages the corpus holds for a question, and how many chunks matched it."""
	passages: list[tuple[Chunk, float]]
	candidate_count: int

	@property
	def needs_discovery(self) -> bool:
		"""Whether too few chunks matched, or the best passage scored too low, to answer from the corpus."""
		if self.candidate_count < settings.DISCOVERY_MIN_CANDIDATES:
			return True
		return not self.passages or self.passages[0][1] < settings.DISCOVERY_MIN_SCORE


class RetrievalService:
	"""Finds the passages in the corpus that best answer a question."""

	CANDIDATES = 50
	RERANK_CANDIDATES = 20

	@classmethod
	def retrieve(cls, question: str, queries: list[str], top_k: int = RerankService.TOP_K) -> Retrieval:
		"""Searches the chunks with `queries`, reranks the best against `question` and keeps the `top_k`."""
		candidates = list(Chunk.objects.search(*queries).select_related(Chunk.fields.paper)[:cls.CANDIDATES])
		passages = RerankService.rerank(question, candidates[:cls.RERANK_CANDIDATES], top_k)
		return Retrieval(passages=passages, candidate_count=len(candidates))
