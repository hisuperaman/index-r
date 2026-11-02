from unittest.mock import patch

from django.test import SimpleTestCase
from requests import HTTPError

from enums.Paper import PaperSource
from papers.services.fetchers import (
	ArxivFetcherService, OpenAlexFetcherService, OrchestratorFetcherService, SemanticScholarFetcherService,
)
from papers.services.fetchers.definitions import FetchedPaper


def paper(source, external_id, title, doi=None):
	return FetchedPaper(source=source, external_id=external_id, title=title, url=f"https://example.org/{external_id}", doi=doi)


class OrchestratorFetcherServiceTests(SimpleTestCase):
	def search(self, semantic_scholar, openalex, arxiv):
		with (
			patch.object(SemanticScholarFetcherService, "search", **semantic_scholar),
			patch.object(OpenAlexFetcherService, "search", **openalex),
			patch.object(ArxivFetcherService, "search", **arxiv),
		):
			return OrchestratorFetcherService.search("attention", limit_per_provider=5)

	def test_combines_every_provider_in_order(self):
		papers = self.search(
			{"return_value": [paper(PaperSource.SEMANTIC_SCHOLAR, "s1", "First")]},
			{"return_value": [paper(PaperSource.OPENALEX, "o1", "Second")]},
			{"return_value": [paper(PaperSource.ARXIV, "a1", "Third")]},
		)

		self.assertEqual([p.external_id for p in papers], ["s1", "o1", "a1"])

	def test_drops_a_paper_an_earlier_provider_returned(self):
		papers = self.search(
			{"return_value": [paper(PaperSource.SEMANTIC_SCHOLAR, "s1", "Attention Is All You Need", doi="10.1/X")]},
			{"return_value": [paper(PaperSource.OPENALEX, "o1", "Attention is all you need", doi="10.1/x")]},
			{"return_value": [paper(PaperSource.ARXIV, "a1", "Attention is all you need.")]},
		)

		self.assertEqual([p.external_id for p in papers], ["s1"])

	def test_a_failing_provider_does_not_stop_the_others(self):
		with self.assertLogs("papers.services.fetchers.OrchestratorFetcherService", "WARNING"):
			papers = self.search(
				{"side_effect": HTTPError("429 Too Many Requests")},
				{"return_value": [paper(PaperSource.OPENALEX, "o1", "Second")]},
				{"side_effect": ValueError("bad payload")},
			)

		self.assertEqual([p.external_id for p in papers], ["o1"])
