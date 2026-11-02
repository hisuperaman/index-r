from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from enums.Paper import PaperSource
from iam.models import User
from papers.models import Citation, Paper
from papers.services import DiscoveryService, PaperStoreService
from papers.services.fetchers import ArxivFetcherService, OpenAlexFetcherService
from papers.services.fetchers.definitions import FetchedPaper
from workspaces.models import TrackedTopic, TrackingUpdate, Workspace, WorkspacePaper
from workspaces.services import TrackingService

NOW = datetime(2026, 11, 2, 6, tzinfo=UTC)


def paper(external_id: str, source=PaperSource.ARXIV, **fields) -> Paper:
	return Paper.objects.create(
		source=source, external_id=external_id, title=f"Paper {external_id}", url=f"https://example.org/{external_id}",
		**fields,
	)


def fetched(external_id: str) -> FetchedPaper:
	return FetchedPaper(
		source=PaperSource.OPENALEX, external_id=external_id, title=f"Citing {external_id}",
		url=f"https://openalex.org/{external_id}",
	)


class TrackingTestCase(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=cls.user, name="Retrieval")
		cls.other_workspace = Workspace.objects.create(user=cls.user, name="Other")

	def setUp(self):
		self.enterContext(patch("workspaces.services.TrackingService.timezone.now", return_value=NOW))


class CheckTopicTests(TrackingTestCase):

	def setUp(self):
		super().setUp()
		self.topic = TrackedTopic.objects.create(workspace=self.workspace, query="sparse retrieval")
		TrackedTopic.objects.filter(pk=self.topic.pk).update(created_at=NOW)
		self.topic.refresh_from_db()

	def test_a_first_check_looks_back_and_reports_papers_the_workspace_lacks(self):
		new, already_in = paper("2610.00001"), paper("2610.00002")
		WorkspacePaper.objects.create(workspace=self.workspace, paper=already_in)

		with patch.object(DiscoveryService, "discover", return_value=[new, already_in]) as discover:
			TrackingService.check_topic(self.topic)

		discover.assert_called_once_with("sparse retrieval", since=date(2026, 10, 3))
		self.assertEqual(
			list(TrackingUpdate.objects.values_list("workspace", "paper", "topic")),
			[(self.workspace.pk, new.pk, self.topic.pk)],
		)
		self.topic.refresh_from_db()
		self.assertEqual(self.topic.checked_at, NOW)

	def test_a_later_check_starts_from_the_last_one_and_reports_each_paper_once(self):
		found = paper("2610.00001")
		TrackingUpdate.objects.create(workspace=self.workspace, paper=found, topic=self.topic)
		TrackedTopic.objects.filter(pk=self.topic.pk).update(checked_at=NOW - timedelta(days=1))
		self.topic.refresh_from_db()

		with patch.object(DiscoveryService, "discover", return_value=[found]) as discover:
			TrackingService.check_topic(self.topic)

		discover.assert_called_once_with("sparse retrieval", since=date(2026, 11, 1))
		self.assertEqual(TrackingUpdate.objects.count(), 1)


class CheckCitationsTests(TrackingTestCase):

	def setUp(self):
		super().setUp()
		self.tracked = paper("1706.03762")
		for workspace in (self.workspace, self.other_workspace):
			WorkspacePaper.objects.create(workspace=workspace, paper=self.tracked, tracked_at=NOW)
		WorkspacePaper.objects.create(workspace=Workspace.objects.create(user=self.user, name="Untracked"), paper=self.tracked)

	def check(self, citing: list[FetchedPaper], work_id: str | None = "W1"):
		with (
			patch.object(OpenAlexFetcherService, "work_id", return_value=work_id) as lookup,
			patch.object(OpenAlexFetcherService, "citing", return_value=citing) as fetch,
			patch.object(PaperStoreService, "queue_ingestion"),
		):
			TrackingService.check_citations(self.tracked)
		return lookup, fetch

	def test_records_new_citing_papers_for_every_workspace_tracking_the_paper(self):
		lookup, fetch = self.check([fetched("W10"), fetched("W11")])

		lookup.assert_called_once_with("10.48550/arxiv.1706.03762")
		fetch.assert_called_once_with("W1", date(2026, 10, 3), 10)
		citing = set(Paper.objects.filter(external_id__in=["W10", "W11"]).values_list("pk", flat=True))
		self.assertEqual(set(Citation.objects.filter(cited_paper=self.tracked).values_list("citing_paper", flat=True)), citing)
		self.assertEqual(
			set(TrackingUpdate.objects.values_list("workspace", "paper", "cited_paper")),
			{
				(workspace.pk, citing_pk, self.tracked.pk)
				for workspace in (self.workspace, self.other_workspace) for citing_pk in citing
			},
		)
		self.tracked.refresh_from_db()
		self.assertEqual(self.tracked.citations_checked_at, NOW)

	def test_a_known_citation_is_not_reported_again(self):
		self.check([fetched("W10")])

		self.check([fetched("W10")])

		self.assertEqual(TrackingUpdate.objects.count(), 2)

	def test_an_openalex_paper_needs_no_lookup(self):
		self.tracked.source, self.tracked.external_id = PaperSource.OPENALEX, "W99"

		lookup, fetch = self.check([])

		lookup.assert_not_called()
		self.assertEqual(fetch.call_args.args[0], "W99")

	def test_a_paper_openalex_doesnt_know_is_only_marked_checked(self):
		_, fetch = self.check([fetched("W10")], work_id=None)

		fetch.assert_not_called()
		self.assertFalse(TrackingUpdate.objects.exists())
		self.tracked.refresh_from_db()
		self.assertEqual(self.tracked.citations_checked_at, NOW)


class CheckVersionsTests(TrackingTestCase):

	def test_reports_a_revision_to_the_workspaces_tracking_the_paper(self):
		first = datetime(2023, 8, 2, tzinfo=UTC)
		tracked = paper("1706.03762", revised_at=first)
		WorkspacePaper.objects.create(workspace=self.workspace, paper=tracked, tracked_at=NOW)

		with patch.object(ArxivFetcherService, "revisions", return_value={"1706.03762": NOW}) as revisions:
			TrackingService.check_versions([tracked])

		revisions.assert_called_once_with(["1706.03762"])
		self.assertEqual(list(TrackingUpdate.objects.values_list("workspace", "paper", "topic", "cited_paper")), [
			(self.workspace.pk, tracked.pk, None, None),
		])
		tracked.refresh_from_db()
		self.assertEqual(tracked.revised_at, NOW)

	def test_the_first_check_only_notes_the_current_version(self):
		tracked = paper("2005.11401", source=PaperSource.OPENALEX, doi="10.48550/arxiv.2005.11401")
		WorkspacePaper.objects.create(workspace=self.workspace, paper=tracked, tracked_at=NOW)

		with patch.object(ArxivFetcherService, "revisions", return_value={"2005.11401": NOW}):
			TrackingService.check_versions([tracked])

		self.assertFalse(TrackingUpdate.objects.exists())
		tracked.refresh_from_db()
		self.assertEqual(tracked.revised_at, NOW)

	def test_skips_arxiv_when_no_tracked_paper_is_on_it(self):
		with patch.object(ArxivFetcherService, "revisions") as revisions:
			TrackingService.check_versions([paper("W1", source=PaperSource.OPENALEX)])

		revisions.assert_not_called()


class TrackedPapersTests(TrackingTestCase):

	def test_lists_shared_papers_some_workspace_tracks(self):
		tracked, untracked = paper("1"), paper("2")
		upload = Paper.objects.create(source=PaperSource.UPLOAD, external_id="u", title="Mine", owner=self.user)
		WorkspacePaper.objects.create(workspace=self.workspace, paper=tracked, tracked_at=NOW)
		WorkspacePaper.objects.create(workspace=self.other_workspace, paper=tracked, tracked_at=NOW)
		WorkspacePaper.objects.create(workspace=self.workspace, paper=untracked)
		WorkspacePaper.objects.create(workspace=self.workspace, paper=upload, tracked_at=NOW)

		self.assertEqual(list(TrackingService.tracked_papers()), [tracked])

	def test_check_all_keeps_going_when_one_check_fails(self):
		TrackedTopic.objects.create(workspace=self.workspace, query="a")
		TrackedTopic.objects.create(workspace=self.workspace, query="b")

		with (
			patch.object(TrackingService, "check_topic", side_effect=[RuntimeError("provider down"), None]) as check,
			patch.object(TrackingService, "check_versions"),
			self.assertLogs("workspaces.services.TrackingService", "ERROR"),
		):
			TrackingService.check_all()

		self.assertEqual(check.call_count, 2)
