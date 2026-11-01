from unittest.mock import patch

from django.test import TestCase

from enums.Paper import PaperSource
from papers.models import Paper
from papers.services import DiscoveryService, QueryExpansionService, RerankService
from papers.services.fetchers import OrchestratorFetcherService
from papers.services.fetchers.definitions import FetchedPaper

QUESTION = "How does multi-head attention work?"


def fetched(external_id: str, title: str, abstract: str | None = None, doi: str | None = None) -> FetchedPaper:
	return FetchedPaper(
		source=PaperSource.ARXIV, external_id=external_id, title=title, abstract=abstract, doi=doi,
		url=f"https://arxiv.org/abs/{external_id}",
	)


ATTENTION = fetched("1706.03762", "Attention Is All You Need", "The Transformer.", doi="10.1/attention")
BERT = fetched("1810.04805", "BERT", "Deep bidirectional transformers.")
GARDENING = fetched("0000.00001", "Tomato Gardening", "Growing tomatoes.")


class DiscoveryFetchTests(TestCase):

	def test_searches_every_query_and_drops_repeats_across_queries(self):
		results = {"multi-head attention": [ATTENTION], "transformer": [fetched("W1", "Attention is all you need"), BERT]}

		with patch.object(OrchestratorFetcherService, "search", side_effect=lambda query, limit: results[query]) as search:
			papers = DiscoveryService.fetch(["multi-head attention", "transformer"])

		self.assertEqual(papers, [ATTENTION, BERT])
		search.assert_any_call("transformer", DiscoveryService.LIMIT_PER_PROVIDER)


class DiscoveryFilterRelevantTests(TestCase):

	def test_keeps_papers_scored_at_least_the_minimum_best_first(self):
		with (
			self.settings(DISCOVERY_ABSTRACT_MIN_SCORE=0.3),
			patch.object(RerankService, "score", return_value=[(1, 0.9), (0, 0.3), (2, 0.29)]) as score,
		):
			papers = DiscoveryService.filter_relevant(QUESTION, [ATTENTION, BERT, GARDENING])

		self.assertEqual(papers, [BERT, ATTENTION])
		score.assert_called_once_with(QUESTION, [
			"Attention Is All You Need\nThe Transformer.",
			"BERT\nDeep bidirectional transformers.",
			"Tomato Gardening\nGrowing tomatoes.",
		])

	def test_judges_a_paper_without_an_abstract_on_its_title(self):
		with patch.object(RerankService, "score", return_value=[]) as score:
			DiscoveryService.filter_relevant(QUESTION, [fetched("1", "Attention")])

		score.assert_called_once_with(QUESTION, ["Attention"])


class DiscoverTests(TestCase):

	def discover(self, queries: list[str] | None = None) -> list[Paper]:
		with (
			self.settings(DISCOVERY_ABSTRACT_MIN_SCORE=0.5),
			patch.object(OrchestratorFetcherService, "search", return_value=[ATTENTION, GARDENING]),
			patch.object(RerankService, "score", return_value=[(0, 0.9), (1, 0.01)]),
		):
			return DiscoveryService.discover(QUESTION, queries)

	def test_stores_only_the_relevant_papers(self):
		papers = self.discover(["multi-head attention"])

		self.assertEqual([paper.title for paper in papers], ["Attention Is All You Need"])
		self.assertQuerySetEqual(Paper.objects.values_list("title", flat=True), ["Attention Is All You Need"])

	def test_expands_the_question_when_no_queries_are_given(self):
		with patch.object(QueryExpansionService, "expand", return_value=["multi-head attention"]) as expand:
			self.discover()

		expand.assert_called_once_with(QUESTION)
