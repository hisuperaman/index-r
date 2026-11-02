from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import RestrictedError
from django.test import TestCase
from django.utils import timezone

from enums.Paper import PaperSource
from enums.Workspace import MessageRole
from papers.models import Chunk, Paper
from workspaces.models import Message, MessageCitation, TrackedTopic, Workspace, WorkspacePaper


class WorkspacePaperTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="owner@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=user, name="Retrieval")
		cls.paper = Paper.objects.create(
			source=PaperSource.ARXIV,
			external_id="1706.03762",
			title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)

	def test_workspace_lists_its_papers(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

		self.assertQuerySetEqual(self.workspace.papers.all(), [self.paper])
		self.assertQuerySetEqual(self.paper.workspaces.all(), [self.workspace])

	def test_paper_is_mentioned_once_per_workspace(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

		with self.assertRaises(IntegrityError):
			WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

	def test_deleting_workspace_removes_its_mentions_but_keeps_the_paper(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

		self.workspace.delete()

		self.assertFalse(WorkspacePaper.objects.exists())
		self.assertTrue(Paper.objects.filter(pk=self.paper.pk).exists())

	def test_mentioned_paper_cannot_be_deleted(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

		with self.assertRaises(RestrictedError):
			self.paper.delete()


class WorkspaceTests(TestCase):
	def test_name_cannot_be_blank(self):
		user = get_user_model().objects.create_user(email="owner@example.com", password="password")

		with self.assertRaises(IntegrityError):
			Workspace.objects.create(user=user, name="")


class TrackedTopicTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="owner@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=user, name="Retrieval")

	def test_a_query_is_tracked_once_per_workspace(self):
		TrackedTopic.objects.create(workspace=self.workspace, query="sparse retrieval")

		with self.assertRaises(IntegrityError):
			TrackedTopic.objects.create(workspace=self.workspace, query="sparse retrieval")

	def test_query_cannot_be_blank(self):
		with self.assertRaises(IntegrityError):
			TrackedTopic.objects.create(workspace=self.workspace, query="")

	def test_deleting_the_workspace_removes_its_topics(self):
		TrackedTopic.objects.create(workspace=self.workspace, query="sparse retrieval")

		self.workspace.delete()

		self.assertFalse(TrackedTopic.objects.exists())


class MessageTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="owner@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=user, name="Retrieval")

	def test_content_cannot_be_blank(self):
		with self.assertRaises(IntegrityError):
			Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content="")

	def test_role_must_be_user_or_assistant(self):
		with self.assertRaises(IntegrityError):
			Message.objects.create(workspace=self.workspace, role="system", content="Hello")


class MessageCitationTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="owner@example.com", password="password")
		workspace = Workspace.objects.create(user=user, name="Retrieval")
		cls.message = Message.objects.create(workspace=workspace, role=MessageRole.ASSISTANT, content="Answer [1].")
		cls.paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)
		cls.chunk = Chunk.objects.create(paper=cls.paper, text="Attention.", start_page=1, end_page=1, chunk_index=0)
		cls.other_chunk = Chunk.objects.create(paper=cls.paper, text="Dropout.", start_page=2, end_page=2, chunk_index=1)

	def test_message_lists_the_chunks_it_cites(self):
		MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=1)

		self.assertQuerySetEqual(self.message.cited_chunks.all(), [self.chunk])

	def test_a_number_is_used_once_per_message(self):
		MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=1)

		with self.assertRaises(IntegrityError):
			MessageCitation.objects.create(message=self.message, chunk=self.other_chunk, number=1)

	def test_a_chunk_is_cited_once_per_message(self):
		MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=1)

		with self.assertRaises(IntegrityError):
			MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=2)

	def test_numbers_start_at_one(self):
		with self.assertRaises(IntegrityError):
			MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=0)

	def test_a_cited_chunk_cannot_be_deleted(self):
		MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=1)

		with self.assertRaises(RestrictedError):
			self.chunk.delete()

	def test_deleting_the_message_removes_its_citations(self):
		MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=1)

		self.message.delete()

		self.assertFalse(MessageCitation.objects.exists())


class MentionedPapersTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="owner@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=user, name="Retrieval")
		cls.other_workspace = Workspace.objects.create(user=user, name="Other")

		def paper(external_id: str) -> Paper:
			return Paper.objects.create(
				source=PaperSource.ARXIV, external_id=external_id, title=f"Paper {external_id}",
				url=f"https://arxiv.org/abs/{external_id}",
			)

		cls.attention, cls.bert, cls.uncited = paper("1"), paper("2"), paper("3")
		cls.attention_chunks = [
			Chunk.objects.create(paper=cls.attention, text=f"Text {index}.", start_page=1, end_page=1, chunk_index=index)
			for index in range(2)
		]
		cls.bert_chunk = Chunk.objects.create(paper=cls.bert, text="BERT.", start_page=1, end_page=1, chunk_index=0)

	def cite(self, workspace: Workspace, *chunks: Chunk, days_ago: int = 0) -> Message:
		message = Message.objects.create(workspace=workspace, role=MessageRole.ASSISTANT, content="Answer.")
		Message.objects.filter(pk=message.pk).update(created_at=timezone.now() - timedelta(days=days_ago))
		for number, chunk in enumerate(chunks, start=1):
			MessageCitation.objects.create(message=message, chunk=chunk, number=number)
		return message

	def test_lists_each_cited_paper_once(self):
		self.cite(self.workspace, *self.attention_chunks)
		self.cite(self.workspace, self.attention_chunks[0], self.bert_chunk)

		self.assertQuerySetEqual(self.workspace.mentioned_papers(), [self.attention, self.bert], ordered=False)

	def test_counts_citations_and_keeps_the_latest(self):
		self.cite(self.workspace, *self.attention_chunks, days_ago=3)
		latest = self.cite(self.workspace, self.attention_chunks[0], days_ago=1)
		latest.refresh_from_db()

		paper = self.workspace.mentioned_papers().get()

		self.assertEqual((paper._mention_count, paper._last_mentioned_at), (3, latest.created_at))

	def test_ignores_citations_in_other_workspaces(self):
		self.cite(self.other_workspace, self.bert_chunk)

		self.assertQuerySetEqual(self.workspace.mentioned_papers(), [])

	def test_flags_papers_already_in_the_workspace(self):
		self.cite(self.workspace, self.attention_chunks[0], self.bert_chunk)
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.bert)

		flags = dict(self.workspace.mentioned_papers().values_list("title", "_in_workspace"))

		self.assertEqual(flags, {"Paper 1": False, "Paper 2": True})


class DeletingAUserTests(TestCase):

	def test_removes_their_private_papers_even_when_cited(self):
		user = get_user_model().objects.create_user(email="owner@example.com", password="password")
		paper = Paper.objects.create(source=PaperSource.UPLOAD, external_id="mine", owner=user, title="Mine")
		chunk = Chunk.objects.create(paper=paper, text="Text.", start_page=1, end_page=1, chunk_index=0)
		workspace = Workspace.objects.create(user=user, name="Retrieval")
		WorkspacePaper.objects.create(workspace=workspace, paper=paper)
		message = Message.objects.create(workspace=workspace, role=MessageRole.ASSISTANT, content="A [1].")
		MessageCitation.objects.create(message=message, chunk=chunk, number=1)

		user.delete()

		self.assertFalse(Paper.objects.filter(pk=paper.pk).exists())
