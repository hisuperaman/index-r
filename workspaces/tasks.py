from celery import shared_task

from papers.models import Paper
from workspaces.models import TrackedTopic
from workspaces.services import TrackingService


@shared_task
def check_tracking() -> None:
	"""Queues a check of every tracked topic, every tracked paper's citations, and their arXiv versions."""
	for topic_id in TrackedTopic.objects.values_list(TrackedTopic.fields.id, flat=True):
		check_tracked_topic.delay(topic_id)
	for paper_id in TrackingService.tracked_papers().values_list(Paper.fields.id, flat=True):
		check_paper_citations.delay(paper_id)
	check_paper_versions.delay()


@shared_task
def check_tracked_topic(topic_id: str) -> None:
	"""Checks one tracked topic for new papers."""
	topic = TrackedTopic.objects.filter(pk=topic_id).first()
	if topic is not None:
		TrackingService.check_topic(topic)


@shared_task
def check_paper_citations(paper_id: str) -> None:
	"""Checks one tracked paper for new citing papers."""
	paper = TrackingService.tracked_papers().filter(pk=paper_id).first()
	if paper is not None:
		TrackingService.check_citations(paper)


@shared_task
def check_paper_versions() -> None:
	"""Checks every tracked arXiv paper for a new version."""
	TrackingService.check_versions(list(TrackingService.tracked_papers()))
