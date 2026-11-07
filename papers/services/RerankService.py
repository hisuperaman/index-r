from functools import cache

import cohere
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from papers.models import Chunk


class RerankService:
	"""Scores texts for how well a Cohere cross-encoder judges they answer a question."""

	MODEL = "rerank-v3.5"
	TOP_K = 5

	@classmethod
	def rerank(cls, question: str, chunks: list[Chunk], top_k: int = TOP_K) -> list[tuple[Chunk, float]]:
		"""Returns the `top_k` chunks with their 0–1 relevance score, best first."""
		scores = cls.score(question, [cls.format_passage(chunk) for chunk in chunks], top_k)
		return [(chunks[index], score) for index, score in scores]

	@classmethod
	def score(cls, question: str, documents: list[str], top_k: int | None = None) -> list[tuple[int, float]]:
		"""Returns the index and 0–1 relevance score of the `top_k` best documents (all by default), best first."""
		if not documents:
			return []

		if not settings.COHERE_API_KEY:
			raise ImproperlyConfigured("Set COHERE_API_KEY to rerank passages.")
		response = cls.get_client(settings.COHERE_API_KEY).rerank(
			model=cls.MODEL, query=question, documents=documents, top_n=top_k or len(documents),
		)
		return [(result.index, result.relevance_score) for result in response.results]

	@staticmethod
	@cache
	def get_client(api_key: str) -> cohere.ClientV2:
		"""Returns the Cohere client for this key, building it once."""
		return cohere.ClientV2(api_key=api_key)

	@staticmethod
	def format_passage(chunk: Chunk) -> str:
		"""The chunk's paper title, section heading and text."""
		heading = f" — {chunk.heading}" if chunk.heading else ""
		return f"{chunk.paper.title}{heading}\n{chunk.text}"
