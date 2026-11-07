from datetime import UTC, date, datetime
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from enums.Paper import DatePrecision, PaperSource
from papers.services.fetchers import ArxivFetcherService
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper

FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <published>2017-06-12T17:57:34Z</published>
    <updated>2023-08-02T00:41:18Z</updated>
    <title>Attention Is All
      You Need</title>
    <summary>  The dominant sequence transduction models.
    </summary>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <arxiv:doi>10.48550/arXiv.1706.03762</arxiv:doi>
    <arxiv:journal_ref>NeurIPS 2017</arxiv:journal_ref>
    <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf"/>
  </entry>
  <entry>
    <id>http://arxiv.org/api/errors#incorrect_id_format</id>
    <title>Error</title>
  </entry>
</feed>"""


class ArxivFetcherServiceTests(SimpleTestCase):
	def search(self, query="attention transformer", limit=5):
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=Mock(content=FEED)) as get:
			return ArxivFetcherService.search(query, limit), get

	def test_maps_entries_to_papers(self):
		papers, _ = self.search()

		self.assertEqual(papers, [FetchedPaper(
			source=PaperSource.ARXIV,
			external_id="1706.03762",
			title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
			doi="10.48550/arXiv.1706.03762",
			abstract="The dominant sequence transduction models.",
			venue="NeurIPS 2017",
			publication_date=date(2017, 6, 12),
			publication_date_precision=DatePrecision.DAY,
			pdf_url="http://arxiv.org/pdf/1706.03762v7",
			revised_at=datetime(2023, 8, 2, 0, 41, 18, tzinfo=UTC),
			authors=[FetchedAuthor(name="Ashish Vaswani"), FetchedAuthor(name="Noam Shazeer")],
		)])

	def test_searches_every_term(self):
		_, get = self.search("attention transformer", 5)

		self.assertEqual(get.call_args.kwargs["params"], {
			"search_query": "all:attention AND all:transformer",
			"start": 0,
			"max_results": 5,
		})

	def test_since_limits_to_papers_submitted_from_that_date_newest_first(self):
		with (
			patch("papers.services.fetchers.ArxivFetcherService.timezone.localdate", return_value=date(2026, 11, 2)),
			patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=Mock(content=FEED)) as get,
		):
			ArxivFetcherService.search("attention", 5, since=date(2026, 10, 1))

		self.assertEqual(get.call_args.kwargs["params"], {
			"search_query": "all:attention AND submittedDate:[202610010000 TO 202611022359]",
			"start": 0,
			"max_results": 5,
			"sortBy": "submittedDate",
			"sortOrder": "descending",
		})

	def test_reads_when_each_paper_was_last_revised(self):
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=Mock(content=FEED)) as get:
			revised = ArxivFetcherService.revisions(["1706.03762"])

		self.assertEqual(revised, {"1706.03762": datetime(2023, 8, 2, 0, 41, 18, tzinfo=UTC)})
		self.assertEqual(get.call_args.kwargs["params"], {"id_list": "1706.03762", "max_results": 1})

	def test_asks_for_revisions_in_batches(self):
		ids = [f"2601.{number:05d}" for number in range(ArxivFetcherService.ID_BATCH + 1)]

		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=Mock(content=FEED)) as get:
			ArxivFetcherService.revisions(ids)

		self.assertEqual([call.kwargs["params"]["max_results"] for call in get.call_args_list], [ArxivFetcherService.ID_BATCH, 1])

	def test_skips_ids_arxiv_cannot_have(self):
		with patch("papers.services.fetchers.BaseFetcherService.requests.get", return_value=Mock(content=FEED)) as get:
			ArxivFetcherService.revisions(["1706.03762", "hep-th/9901001", "math.GT/0309136", "paging-0", "W123"])

		self.assertEqual(get.call_args.kwargs["params"]["id_list"], "1706.03762,hep-th/9901001,math.GT/0309136")

	def test_asks_nothing_when_no_id_is_valid(self):
		with patch("papers.services.fetchers.BaseFetcherService.requests.get") as get:
			self.assertEqual(ArxivFetcherService.revisions(["paging-0"]), {})

		get.assert_not_called()

