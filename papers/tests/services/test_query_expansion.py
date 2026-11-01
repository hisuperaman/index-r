from unittest.mock import patch

from django.test import SimpleTestCase

from papers.prompts import QUERY_EXPANSION_INSTRUCTIONS
from papers.schemas import SearchQueries
from papers.services import QueryExpansionService
from server.services import LLMService


class QueryExpansionServiceTests(SimpleTestCase):

	def expand(self, *queries: str) -> list[str]:
		with patch.object(LLMService, "run", return_value=SearchQueries.model_construct(queries=list(queries))) as run:
			result = QueryExpansionService.expand("Which models report F1 above 0.9 on MMLU?")
		self.run = run
		return result

	def test_asks_the_llm_for_search_queries(self):
		self.expand("MMLU F1", "MMLU benchmark results", "massive multitask language understanding")

		self.run.assert_called_once_with(
			"Which models report F1 above 0.9 on MMLU?", SearchQueries, QUERY_EXPANSION_INSTRUCTIONS,
		)

	def test_returns_the_queries_in_order(self):
		self.assertEqual(
			self.expand("MMLU F1", "MMLU benchmark results", "multitask accuracy"),
			["MMLU F1", "MMLU benchmark results", "multitask accuracy"],
		)

	def test_strips_queries_and_drops_blanks_and_repeats(self):
		self.assertEqual(self.expand(" MMLU F1 ", "MMLU F1", "  ", "multitask accuracy"), ["MMLU F1", "multitask accuracy"])
