from datetime import date
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from enums.Paper import DatePrecision, PaperSource
from papers.services.fetchers import OpenAlexFetcherService
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper

WORK = {
	"id": "https://openalex.org/W2963403868",
	"doi": "https://doi.org/10.48550/arxiv.1706.03762",
	"title": "Attention Is All You Need",
	"publication_date": "2017-06-12",
	"cited_by_count": 5000,
	"abstract_inverted_index": {"models": [2], "The": [0], "dominant": [1]},
	"primary_location": {
		"landing_page_url": "https://arxiv.org/abs/1706.03762",
		"pdf_url": None,
		"source": {"display_name": "arXiv"},
	},
	"best_oa_location": {"pdf_url": "https://arxiv.org/pdf/1706.03762"},
	"authorships": [
		{"author": {"display_name": "Ashish Vaswani", "orcid": "https://orcid.org/0000-0001-2345-6789"}},
		{"author": {"display_name": "Noam Shazeer", "orcid": None}},
	],
}


class OpenAlexFetcherServiceTests(SimpleTestCase):
	def search(self, results, limit=5):
		response = Mock(json=Mock(return_value={"results": results}))
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response) as get:
			return OpenAlexFetcherService.search("attention", limit), get

	def test_maps_works_to_papers(self):
		papers, _ = self.search([WORK])

		self.assertEqual(papers, [FetchedPaper(
			source=PaperSource.OPENALEX,
			external_id="W2963403868",
			title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
			doi="10.48550/arxiv.1706.03762",
			abstract="The dominant models",
			venue="arXiv",
			citation_count=5000,
			publication_date=date(2017, 6, 12),
			publication_date_precision=DatePrecision.DAY,
			pdf_url="https://arxiv.org/pdf/1706.03762",
			authors=[
				FetchedAuthor(name="Ashish Vaswani", orcid="0000-0001-2345-6789"),
				FetchedAuthor(name="Noam Shazeer"),
			],
		)])

	def test_skips_works_without_a_title(self):
		papers, _ = self.search([{**WORK, "title": None, "display_name": None}])

		self.assertEqual(papers, [])

	def test_caps_the_page_size(self):
		_, get = self.search([], limit=1000)

		self.assertEqual(get.call_args.kwargs["params"]["per-page"], OpenAlexFetcherService.MAX_LIMIT)
