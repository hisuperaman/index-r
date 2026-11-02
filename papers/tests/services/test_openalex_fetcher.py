from datetime import date
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from requests import HTTPError

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

	def test_since_limits_to_works_published_from_that_date_to_today_newest_first(self):
		response = Mock(json=Mock(return_value={"results": []}))
		with (
			patch("papers.services.fetchers.OpenAlexFetcherService.timezone.localdate", return_value=date(2026, 11, 2)),
			patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response) as get,
		):
			OpenAlexFetcherService.search("attention", 5, since=date(2026, 10, 1))

		self.assertEqual(get.call_args.kwargs["params"], {
			"search": "attention",
			"per-page": 5,
			"filter": "from_publication_date:2026-10-01,to_publication_date:2026-11-02",
			"sort": "publication_date:desc",
		})


class OpenAlexCitationTests(SimpleTestCase):

	def test_lists_the_newest_works_citing_a_work(self):
		response = Mock(json=Mock(return_value={"results": [WORK]}))
		with (
			patch("papers.services.fetchers.OpenAlexFetcherService.timezone.localdate", return_value=date(2026, 11, 2)),
			patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response) as get,
		):
			papers = OpenAlexFetcherService.citing("W1", date(2026, 10, 1), 10)

		self.assertEqual([paper.external_id for paper in papers], ["W2963403868"])
		self.assertEqual(get.call_args.kwargs["params"], {
			"filter": "cites:W1,from_publication_date:2026-10-01,to_publication_date:2026-11-02",
			"sort": "publication_date:desc",
			"per-page": 10,
		})

	def test_finds_a_works_id_by_doi(self):
		response = Mock(json=Mock(return_value={"id": "https://openalex.org/W2626778328"}))
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response) as get:
			work_id = OpenAlexFetcherService.work_id("10.48550/arxiv.1706.03762")

		self.assertEqual(work_id, "W2626778328")
		self.assertEqual(get.call_args.args[0], "https://api.openalex.org/works/doi:10.48550/arxiv.1706.03762")

	def test_an_unknown_doi_has_no_work_id(self):
		response = Mock(status_code=404)
		response.raise_for_status.side_effect = HTTPError(response=response)
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response):
			self.assertIsNone(OpenAlexFetcherService.work_id("10.1/unknown"))
