from papers.prompts import QUERY_EXPANSION_INSTRUCTIONS
from papers.schemas import SearchQueries
from server.services import LLMService


class QueryExpansionService:
	"""Turns a research question into keyword queries for full-text search."""

	@staticmethod
	def expand(question: str) -> list[str]:
		"""Returns the LLM's keyword queries for `question`, stripped and without repeats."""
		queries = LLMService.run(question, SearchQueries, QUERY_EXPANSION_INSTRUCTIONS).queries
		return list(dict.fromkeys(query.strip() for query in queries if query.strip()))
