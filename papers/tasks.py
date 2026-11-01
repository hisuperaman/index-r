import logging
from functools import partial

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from papers.models import Paper
from papers.services import PdfDownloadService, TextExtractorService

logger = logging.getLogger(__name__)


@shared_task
def ingest_paper(paper_id: str) -> None:
	"""Downloads a pending paper's PDF and stores its chunks, marking the paper completed or failed."""
	paper = Paper.objects.pending().filter(pk=paper_id).first()
	if paper is None:
		return

	try:
		if not paper.pdf_url:
			raise ValueError("The paper has no open-access PDF")
		with PdfDownloadService.download(paper.pdf_url) as path:
			extracted = TextExtractorService.extract(path)
	except Exception:
		logger.exception("Ingestion failed for paper %s", paper.pk)
		Paper.objects.filter(pk=paper.pk).update(ingestion_failed_at=timezone.now())
		return

	with transaction.atomic():
		paper.replace_chunks(extracted.chunks)
		Paper.objects.filter(pk=paper.pk).update(ingested_at=timezone.now())


def queue_ingest_paper(paper: Paper) -> None:
	"""Queues the paper's ingestion once the surrounding transaction commits."""
	transaction.on_commit(partial(ingest_paper.delay, paper.pk), robust=True)
