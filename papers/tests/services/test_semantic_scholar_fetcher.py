from datetime import date
from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from enums.Paper import DatePrecision, PaperSource
from papers.services.fetchers import SemanticScholarFetcherService
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper

PAPER = {
	"paperId": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
	"title": "Attention is All you Need",
	"abstract": "The dominant sequence transduction models.",
	"url": "https://www.semanticscholar.org/paper/204e3073870fae3d05bcbc2f6a8e263d9b72e776",
	"venue": "Neural Information Processing Systems",
	"year": 2017,
	"publicationDate": None,
	"citationCount": 100000,
	"externalIds": {"DOI": "10.48550/arXiv.1706.03762", "ArXiv": "1706.03762"},
	"openAccessPdf": {"url": "", "status": None},
	"authors": [{"authorId": "40348417", "name": "Ashish Vaswani"}],
}


class SemanticScholarFetcherServiceTests(SimpleTestCase):
	def search(self, data):
		response = Mock(json=Mock(return_value={"total": len(data), "data": data}))
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response):
			return SemanticScholarFetcherService.search("attention", 5)

	def test_maps_results_to_papers(self):
		self.assertEqual(self.search([PAPER]), [FetchedPaper(
			source=PaperSource.SEMANTIC_SCHOLAR,
			external_id="204e3073870fae3d05bcbc2f6a8e263d9b72e776",
			title="Attention is All you Need",
			url="https://www.semanticscholar.org/paper/204e3073870fae3d05bcbc2f6a8e263d9b72e776",
			doi="10.48550/arXiv.1706.03762",
			abstract="The dominant sequence transduction models.",
			venue="Neural Information Processing Systems",
			citation_count=100000,
			publication_date=date(2017, 1, 1),
			publication_date_precision=DatePrecision.YEAR,
			authors=[FetchedAuthor(name="Ashish Vaswani")],
		)])

	def test_since_limits_to_papers_published_from_that_date(self):
		response = Mock(json=Mock(return_value={"data": []}))
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response) as get:
			SemanticScholarFetcherService.search("attention", 5, since=date(2026, 10, 1))

		self.assertEqual(get.call_args.kwargs["params"]["publicationDateOrYear"], "2026-10-01:")

	def test_uses_the_full_publication_date_when_given(self):
		paper = self.search([{**PAPER, "publicationDate": "2017-06-12"}])[0]

		self.assertEqual((paper.publication_date, paper.publication_date_precision), (date(2017, 6, 12), DatePrecision.DAY))

	def test_handles_no_results(self):
		response = Mock(json=Mock(return_value={"total": 0}))
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response):
			self.assertEqual(SemanticScholarFetcherService.search("nothing", 5), [])


def response(status: int) -> MagicMock:
	mock = MagicMock(status_code=status)
	mock.json.return_value = {"data": []}
	return mock


class SemanticScholarApiKeyTests(SimpleTestCase):

	def test_sends_the_semantic_scholar_key_when_set(self):
		with (
			self.settings(SEMANTIC_SCHOLAR_API_KEY="s2-key"),
			patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response(200)) as get,
		):
			SemanticScholarFetcherService.search("attention", 3)

		self.assertEqual(get.call_args.kwargs["headers"], {"x-api-key": "s2-key"})

	def test_sends_no_key_when_unset(self):
		with (
			self.settings(SEMANTIC_SCHOLAR_API_KEY=None),
			patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=response(200)) as get,
		):
			SemanticScholarFetcherService.search("attention", 3)

		self.assertEqual(get.call_args.kwargs["headers"], {})
