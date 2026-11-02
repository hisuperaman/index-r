import logging
from functools import partial

from datetime import timedelta

from celery import shared_task
from django.conf import settings
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


@shared_task
def requeue_stale_ingestions() -> None:
	"""Queues again the papers whose ingestion was queued long ago but never finished, such as after a worker restart."""
	stale = timezone.now() - timedelta(minutes=settings.INGESTION_STALE_MINUTES)
	papers = Paper.objects.pending().exclude(pdf_url=None).exclude(pdf_url="").filter(created_at__lt=stale)
	for paper_id in papers.values_list(Paper.fields.id, flat=True):
		ingest_paper.delay(paper_id)


def queue_ingest_paper(paper: Paper) -> None:
	"""Queues the paper's ingestion once the surrounding transaction commits."""
	transaction.on_commit(partial(ingest_paper.delay, paper.pk), robust=True)
