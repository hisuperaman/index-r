import logging
from datetime import date, timedelta

from django.conf import settings
from django.db.models import Exists, OuterRef
from django.utils import timezone

from enums.Paper import PaperSource
from papers.models import Citation, Paper
from papers.services import DiscoveryService, PaperStoreService
from papers.services.fetchers import ArxivFetcherService, OpenAlexFetcherService
from workspaces.models import TrackedTopic, TrackingUpdate, WorkspacePaper

logger = logging.getLogger(__name__)


class TrackingService:
	"""Checks tracked topics and papers for what's new, recording it as updates for their workspaces."""

	@staticmethod
	def tracked_papers():
		"""Shared-corpus papers that at least one workspace tracks."""
		tracked = WorkspacePaper.objects.filter(paper=OuterRef(Paper.fields.id), tracked_at__isnull=False)
		return Paper.objects.public().filter(Exists(tracked))

	@staticmethod
	def since(checked_at, created_at) -> date:
		"""The day a check starts from: the last check, or the lookback window before the first one."""
		return (checked_at or created_at - timedelta(days=settings.TRACKING_LOOKBACK_DAYS)).date()

	@classmethod
	def check_all(cls) -> None:
		"""Checks every tracked topic and paper now, logging the ones that fail."""
		for topic in TrackedTopic.objects.all():
			try:
				cls.check_topic(topic)
			except Exception:
				logger.exception("Checking tracked topic %s failed", topic.pk)
		papers = list(cls.tracked_papers())
		for paper in papers:
			try:
				cls.check_citations(paper)
			except Exception:
				logger.exception("Checking citations of paper %s failed", paper.pk)
		try:
			cls.check_versions(papers)
		except Exception:
			logger.exception("Checking arXiv versions failed")

	@classmethod
	def check_topic(cls, topic: TrackedTopic) -> None:
		"""Finds relevant papers published since the topic was last checked that its workspace doesn't have."""
		started = timezone.now()
		papers = DiscoveryService.discover(topic.query, since=cls.since(topic.checked_at, topic.created_at))
		in_workspace = set(
			WorkspacePaper.objects.filter(workspace_id=topic.workspace_id, paper__in=papers)
			.values_list(WorkspacePaper.fields.paper, flat=True)
		)
		TrackingUpdate.objects.bulk_create(
			[
				TrackingUpdate(workspace_id=topic.workspace_id, topic=topic, paper=paper)
				for paper in papers if paper.pk not in in_workspace
			],
			ignore_conflicts=True,
		)
		TrackedTopic.objects.filter(pk=topic.pk).update(checked_at=started)

	@classmethod
	def check_citations(cls, paper: Paper) -> None:
		"""Finds the newest papers citing `paper` since it was last checked, for every workspace tracking it."""
		started = timezone.now()
		work_id = cls.openalex_id(paper)
		if work_id:
			fetched = OpenAlexFetcherService.citing(
				work_id, cls.since(paper.citations_checked_at, started), settings.TRACKING_MAX_CITATIONS,
			)
			citing = {stored.pk: stored for stored in PaperStoreService.store(fetched) if stored.pk != paper.pk}
			known = set(
				Citation.objects.filter(cited_paper=paper, citing_paper__in=citing)
				.values_list(Citation.fields.citing_paper, flat=True)
			)
			new = [citing_paper for pk, citing_paper in citing.items() if pk not in known]
			Citation.objects.bulk_create(
				[Citation(citing_paper=citing_paper, cited_paper=paper) for citing_paper in new], ignore_conflicts=True,
			)
			TrackingUpdate.objects.bulk_create(
				[
					TrackingUpdate(workspace_id=workspace_id, paper=citing_paper, cited_paper=paper)
					for workspace_id in cls.tracking_workspace_ids(paper) for citing_paper in new
				],
				ignore_conflicts=True,
			)
		Paper.objects.filter(pk=paper.pk).update(citations_checked_at=started)

	@classmethod
	def check_versions(cls, papers: list[Paper]) -> None:
		"""Records a new-version update for each tracked arXiv paper revised since it was last seen."""
		by_arxiv_id = {paper.arxiv_id: paper for paper in papers if paper.arxiv_id}
		if not by_arxiv_id:
			return
		for arxiv_id, revised_at in ArxivFetcherService.revisions(list(by_arxiv_id)).items():
			paper = by_arxiv_id.get(arxiv_id)
			if paper is None or paper.revised_at == revised_at:
				continue
			if paper.revised_at and revised_at > paper.revised_at:
				TrackingUpdate.objects.bulk_create([
					TrackingUpdate(workspace_id=workspace_id, paper=paper)
					for workspace_id in cls.tracking_workspace_ids(paper)
				])
			Paper.objects.filter(pk=paper.pk).update(revised_at=revised_at)

	@staticmethod
	def openalex_id(paper: Paper) -> str | None:
		"""The paper's OpenAlex work ID, looked up by DOI when it came from another source."""
		if paper.source == PaperSource.OPENALEX:
			return paper.external_id
		return OpenAlexFetcherService.work_id(paper.lookup_doi) if paper.lookup_doi else None

	@staticmethod
	def tracking_workspace_ids(paper: Paper) -> list:
		return list(
			WorkspacePaper.objects.filter(paper=paper, tracked_at__isnull=False)
			.values_list(WorkspacePaper.fields.workspace, flat=True)
		)
