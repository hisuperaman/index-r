from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from enums.Paper import PaperSource
from iam.models import User
from papers.models import Paper
from workspaces import tasks
from workspaces.models import TrackedTopic, Workspace, WorkspacePaper
from workspaces.services import TrackingService


class CheckTrackingTests(TestCase):

	def test_queues_a_check_for_every_topic_and_tracked_paper(self):
		user = User.objects.create_user(email="ada@example.com", password="password")
		workspace = Workspace.objects.create(user=user, name="Retrieval")
		topic = TrackedTopic.objects.create(workspace=workspace, query="sparse retrieval")
		paper = Paper.objects.create(source=PaperSource.ARXIV, external_id="1", title="P", url="https://arxiv.org/abs/1")
		WorkspacePaper.objects.create(workspace=workspace, paper=paper, tracked_at=timezone.now())

		with (
			patch.object(tasks.check_tracked_topic, "delay") as topic_check,
			patch.object(tasks.check_paper_citations, "delay") as citation_check,
			patch.object(tasks.check_paper_versions, "delay") as version_check,
		):
			tasks.check_tracking()

		topic_check.assert_called_once_with(topic.pk)
		citation_check.assert_called_once_with(paper.pk)
		version_check.assert_called_once_with()

	def test_a_removed_topic_or_untracked_paper_is_skipped(self):
		with (
			patch.object(TrackingService, "check_topic") as check_topic,
			patch.object(TrackingService, "check_citations") as check_citations,
		):
			tasks.check_tracked_topic("00000000-0000-0000-0000-000000000000")
			tasks.check_paper_citations("00000000-0000-0000-0000-000000000000")

		check_topic.assert_not_called()
		check_citations.assert_not_called()
