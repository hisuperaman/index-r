from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

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

		with self.assertRaises(ProtectedError):
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

		with self.assertRaises(ProtectedError):
			self.chunk.delete()

	def test_deleting_the_message_removes_its_citations(self):
		MessageCitation.objects.create(message=self.message, chunk=self.chunk, number=1)

		self.message.delete()

		self.assertFalse(MessageCitation.objects.exists())
