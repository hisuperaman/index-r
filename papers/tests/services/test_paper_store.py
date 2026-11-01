from datetime import date
from unittest.mock import patch

from django.test import TestCase

from enums.Paper import DatePrecision, PaperSource
from papers.models import Author, Paper
from papers import tasks
from papers.services import PaperStoreService
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper


def fetched_paper(**overrides) -> FetchedPaper:
	values = dict(
		source=PaperSource.ARXIV,
		external_id="1706.03762",
		title="Attention Is All You Need",
		url="https://arxiv.org/abs/1706.03762",
		doi="10.48550/arXiv.1706.03762",
		citation_count=100,
		publication_date=date(2017, 6, 12),
		publication_date_precision=DatePrecision.DAY,
		authors=[FetchedAuthor(name="Ashish Vaswani", orcid="0000-0001-2345-6789"), FetchedAuthor(name="Noam Shazeer")],
	)
	return FetchedPaper(**{**values, **overrides})


class PaperStoreServiceTests(TestCase):

	def test_stores_a_new_paper_with_its_authors_in_byline_order(self):
		[paper] = PaperStoreService.store([fetched_paper()])

		paper.refresh_from_db()
		self.assertEqual((paper.title, paper.doi, paper.citation_count), (
			"Attention Is All You Need", "10.48550/arxiv.1706.03762", 100,
		))
		self.assertQuerySetEqual(
			paper.paper_authors.values_list("order", "author__name", "author__orcid"),
			[(1, "Ashish Vaswani", "0000-0001-2345-6789"), (2, "Noam Shazeer", None)],
		)

	def test_a_paper_from_the_same_source_is_stored_once(self):
		first = PaperStoreService.store_one(fetched_paper())

		second = PaperStoreService.store_one(fetched_paper())

		self.assertEqual(second, first)
		self.assertEqual(Paper.objects.count(), 1)
		self.assertEqual(Author.objects.count(), 2)

	def test_a_paper_from_another_source_with_the_same_doi_is_stored_once(self):
		first = PaperStoreService.store_one(fetched_paper())

		second = PaperStoreService.store_one(fetched_paper(
			source=PaperSource.OPENALEX, external_id="W2963403868", doi="10.48550/ARXIV.1706.03762",
		))

		self.assertEqual(second, first)
		self.assertEqual(Paper.objects.count(), 1)

	def test_a_repeat_fills_blank_fields_and_keeps_the_higher_citation_count(self):
		PaperStoreService.store_one(fetched_paper(abstract=None, pdf_url=None, citation_count=100))

		paper = PaperStoreService.store_one(fetched_paper(
			abstract="The dominant sequence transduction models.", pdf_url="https://arxiv.org/pdf/1706.03762",
			citation_count=90,
		))

		paper.refresh_from_db()
		self.assertEqual(paper.abstract, "The dominant sequence transduction models.")
		self.assertEqual(paper.pdf_url, "https://arxiv.org/pdf/1706.03762")
		self.assertEqual(paper.citation_count, 100)

	def test_a_repeat_keeps_fields_already_set(self):
		PaperStoreService.store_one(fetched_paper(abstract="Original abstract."))

		paper = PaperStoreService.store_one(fetched_paper(abstract="Another abstract."))

		paper.refresh_from_db()
		self.assertEqual(paper.abstract, "Original abstract.")

	def test_reuses_an_author_by_orcid_then_by_name(self):
		PaperStoreService.store_one(fetched_paper())

		paper = PaperStoreService.store_one(fetched_paper(
			external_id="1810.04805", doi=None, title="BERT",
			authors=[FetchedAuthor(name="A. Vaswani", orcid="0000-0001-2345-6789"), FetchedAuthor(name="Noam Shazeer")],
		))

		self.assertEqual(Author.objects.count(), 2)
		self.assertQuerySetEqual(
			paper.paper_authors.values_list("author__name", flat=True), ["Ashish Vaswani", "Noam Shazeer"],
		)

	def test_an_author_listed_twice_is_linked_once(self):
		paper = PaperStoreService.store_one(fetched_paper(
			authors=[FetchedAuthor(name="Noam Shazeer"), FetchedAuthor(name="Noam Shazeer")],
		))

		self.assertQuerySetEqual(paper.paper_authors.values_list("order", "author__name"), [(1, "Noam Shazeer")])

	def test_a_paper_without_a_doi_is_matched_by_source_id_only(self):
		PaperStoreService.store_one(fetched_paper(doi=None))
		PaperStoreService.store_one(fetched_paper(source=PaperSource.OPENALEX, external_id="W1", doi=None))

		self.assertEqual(Paper.objects.count(), 2)


class PaperStoreIngestionQueueTests(TestCase):

	def store(self, fetched: FetchedPaper):
		with patch.object(tasks.ingest_paper, "delay") as delay, self.captureOnCommitCallbacks(execute=True):
			paper = PaperStoreService.store_one(fetched)
		return paper, delay

	def test_queues_a_new_paper_with_a_pdf(self):
		paper, delay = self.store(fetched_paper(pdf_url="https://arxiv.org/pdf/1706.03762"))

		delay.assert_called_once_with(paper.pk)

	def test_does_not_queue_a_new_paper_without_a_pdf(self):
		_, delay = self.store(fetched_paper(pdf_url=None))

		delay.assert_not_called()

	def test_does_not_queue_a_paper_already_stored(self):
		self.store(fetched_paper(pdf_url="https://arxiv.org/pdf/1706.03762"))

		_, delay = self.store(fetched_paper(pdf_url="https://arxiv.org/pdf/1706.03762"))

		delay.assert_not_called()
