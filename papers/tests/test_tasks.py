from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from enums.Paper import IngestionStatus, PaperSource
from papers.definitions import ExtractedChunk, ExtractedPaper
from papers.models import Chunk, Paper
from papers.services import PdfDownloadError, PdfDownloadService, TextExtractorService
from papers.tasks import ingest_paper

PDF_URL = "https://arxiv.org/pdf/1706.03762"


@contextmanager
def fake_download(url):
	yield Path("/tmp/paper.pdf")


EXTRACTED = ExtractedPaper(title="Attention Is All You Need", chunks=[
	ExtractedChunk(heading="Introduction", text="Attention mechanisms.", start_page=1, end_page=1, chunk_index=0),
])


class IngestPaperTests(TestCase):
	def setUp(self):
		self.paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762", pdf_url=PDF_URL,
		)

	def test_stores_the_chunks_and_marks_the_paper_completed(self):
		with (
			patch.object(PdfDownloadService, "download", side_effect=fake_download) as download,
			patch.object(TextExtractorService, "extract", return_value=EXTRACTED) as extract,
		):
			ingest_paper(self.paper.pk)

		self.paper.refresh_from_db()
		self.assertEqual(self.paper.ingestion_status, IngestionStatus.COMPLETED)
		self.assertQuerySetEqual(Chunk.objects.values_list("heading", flat=True), ["Introduction"])
		download.assert_called_once_with(PDF_URL)
		extract.assert_called_once_with(Path("/tmp/paper.pdf"))

	def test_marks_the_paper_failed_when_the_download_fails(self):
		with (
			patch.object(PdfDownloadService, "download", side_effect=PdfDownloadError("not a PDF")),
			self.assertLogs("papers.tasks", "ERROR"),
		):
			ingest_paper(self.paper.pk)

		self.paper.refresh_from_db()
		self.assertEqual(self.paper.ingestion_status, IngestionStatus.FAILED)
		self.assertFalse(Chunk.objects.exists())

	def test_marks_a_paper_without_a_pdf_failed(self):
		Paper.objects.filter(pk=self.paper.pk).update(pdf_url=None)

		with patch.object(PdfDownloadService, "download") as download, self.assertLogs("papers.tasks", "ERROR"):
			ingest_paper(self.paper.pk)

		self.paper.refresh_from_db()
		self.assertEqual(self.paper.ingestion_status, IngestionStatus.FAILED)
		download.assert_not_called()

	def test_skips_a_paper_that_is_no_longer_pending(self):
		Paper.objects.filter(pk=self.paper.pk).update(ingested_at=timezone.now())

		with patch.object(PdfDownloadService, "download") as download:
			ingest_paper(self.paper.pk)

		download.assert_not_called()

	def test_skips_a_paper_whose_ingestion_already_failed(self):
		Paper.objects.filter(pk=self.paper.pk).update(ingestion_failed_at=timezone.now())

		with patch.object(PdfDownloadService, "download") as download:
			ingest_paper(self.paper.pk)

		download.assert_not_called()

	def test_skips_a_paper_deleted_since_it_was_queued(self):
		paper_id = self.paper.pk
		self.paper.delete()

		with patch.object(PdfDownloadService, "download") as download:
			ingest_paper(paper_id)

		download.assert_not_called()
