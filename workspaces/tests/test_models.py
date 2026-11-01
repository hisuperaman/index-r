from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from enums.Paper import PaperSource
from papers.models import Paper
from workspaces.models import Workspace, WorkspacePaper


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
