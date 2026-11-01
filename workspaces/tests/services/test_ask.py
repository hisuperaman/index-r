from contextlib import ExitStack
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from enums.Paper import PaperSource
from enums.Workspace import AskStage, MessageRole
from papers.models import Chunk, Paper
from papers.services import (
	Answer, AnswerService, DiscoveryService, QueryExpansionService, Retrieval, RetrievalService,
)
from workspaces.models import Message, Workspace, WorkspacePaper
from workspaces.services import AskDelta, AskDone, AskService, AskStatus

QUESTION = "How does multi-head attention work?"
QUERIES = ["multi-head attention", "transformer attention heads", "scaled dot-product attention"]


class AskServiceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="ada@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=user, name="Retrieval")
		cls.paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762", ingested_at=timezone.now(),
		)
		cls.chunk = Chunk.objects.create(
			paper=cls.paper, heading="Multi-Head Attention", text="Heads attend jointly.", start_page=4, end_page=4,
			chunk_index=0,
		)

	def setUp(self):
		self.question = Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content=QUESTION)
		self.confident = Retrieval(passages=[(self.chunk, 0.9)], candidate_count=10)
		self.weak = Retrieval(passages=[], candidate_count=0)
		self.answers = [
			Answer(content="Heads", citations={}, is_insufficient_context=False),
			Answer(content="Heads attend jointly [1].", citations={1: self.chunk}, is_insufficient_context=False),
		]

	def ask(self, retrievals: list[Retrieval], discovered: list[Paper] | None = None):
		with ExitStack() as stack:
			stack.enter_context(patch.object(QueryExpansionService, "expand", return_value=QUERIES))
			self.retrieve = stack.enter_context(patch.object(RetrievalService, "retrieve", side_effect=retrievals))
			self.discover = stack.enter_context(patch.object(DiscoveryService, "discover", return_value=discovered or []))
			self.wait = stack.enter_context(patch.object(AskService, "wait_for_ingestion"))
			self.stream = stack.enter_context(patch.object(AnswerService, "stream", return_value=iter(self.answers)))
			return list(AskService.ask(self.question))

	def test_answers_from_the_corpus_when_it_is_confident(self):
		events = self.ask([self.confident])

		self.assertEqual(events[:-1], [
			AskStatus(AskStage.EXPANDING),
			AskStatus(AskStage.SEARCHING),
			AskStatus(AskStage.ANSWERING),
			AskDelta("Heads"),
			AskDelta("Heads attend jointly [1]."),
		])
		self.discover.assert_not_called()
		self.retrieve.assert_called_once_with(QUESTION, QUERIES)
		self.stream.assert_called_once_with(QUESTION, [self.chunk])

	def test_saves_the_answer_with_its_citations_and_cited_papers(self):
		events = self.ask([self.confident])

		message = events[-1].message
		self.assertIsInstance(events[-1], AskDone)
		self.assertEqual(
			(message.workspace, message.role, message.content),
			(self.workspace, MessageRole.ASSISTANT, "Heads attend jointly [1]."),
		)
		self.assertQuerySetEqual(message.citations.values_list("number", "chunk"), [(1, self.chunk.pk)])
		self.assertQuerySetEqual(self.workspace.papers.all(), [self.paper])

	def test_a_paper_already_in_the_workspace_is_not_added_twice(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

		self.ask([self.confident])

		self.assertEqual(WorkspacePaper.objects.filter(workspace=self.workspace).count(), 1)

	def test_discovers_waits_for_new_papers_and_searches_again_when_the_corpus_is_weak(self):
		new_paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="2005.14165", title="GPT-3", url="https://arxiv.org/abs/2005.14165",
		)

		events = self.ask([self.weak, self.confident], discovered=[new_paper, self.paper])

		self.assertEqual([event.stage for event in events if isinstance(event, AskStatus)], [
			AskStage.EXPANDING, AskStage.SEARCHING, AskStage.DISCOVERING, AskStage.INGESTING, AskStage.SEARCHING,
			AskStage.ANSWERING,
		])
		self.discover.assert_called_once_with(QUESTION, QUERIES)
		self.wait.assert_called_once_with([new_paper.pk])
		self.assertEqual(self.retrieve.call_count, 2)

	def test_skips_waiting_when_discovery_finds_nothing_new(self):
		events = self.ask([self.weak], discovered=[self.paper])

		self.assertNotIn(AskStatus(AskStage.INGESTING), events)
		self.wait.assert_not_called()
		self.assertEqual(self.retrieve.call_count, 1)


class WaitForIngestionTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)

	def test_returns_once_no_paper_is_pending(self):
		def ingest(seconds):
			Paper.objects.filter(pk=self.paper.pk).update(ingested_at=timezone.now())

		with patch("workspaces.services.AskService.time.sleep", side_effect=ingest) as sleep:
			AskService.wait_for_ingestion([self.paper.pk])

		sleep.assert_called_once_with(AskService.POLL_SECONDS)

	def test_gives_up_after_the_wait(self):
		with (
			self.settings(INGESTION_WAIT_SECONDS=2),
			patch("workspaces.services.AskService.time.monotonic", side_effect=[0, 1, 2]),
			patch("workspaces.services.AskService.time.sleep") as sleep,
		):
			AskService.wait_for_ingestion([self.paper.pk])

		self.assertEqual(sleep.call_count, 1)
