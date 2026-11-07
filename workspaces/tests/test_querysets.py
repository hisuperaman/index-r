from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from enums.Paper import PaperSource
from enums.Workspace import MessageRole
from papers.models import Paper
from workspaces.models import Message, TrackedTopic, TrackingUpdate, Workspace, WorkspacePaper


class WorkspaceWithActivityTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="ada@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=user, name="Retrieval")
		cls.empty = Workspace.objects.create(user=user, name="Empty")
		for index in range(2):
			paper = Paper.objects.create(
				source=PaperSource.ARXIV, external_id=str(index), title=f"Paper {index}", url=f"https://arxiv.org/abs/{index}",
			)
			WorkspacePaper.objects.create(workspace=cls.workspace, paper=paper)
		for content in ("First?", "Second?", "Third?"):
			Message.objects.create(workspace=cls.workspace, role=MessageRole.USER, content=content)
		cls.answer = Message.objects.create(workspace=cls.workspace, role=MessageRole.ASSISTANT, content="Answer.")

	def annotated(self, workspace: Workspace) -> Workspace:
		return Workspace.objects.with_activity().get(pk=workspace.pk)

	def test_counts_papers_and_questions_without_multiplying(self):
		workspace = self.annotated(self.workspace)

		self.assertEqual((workspace.paper_count, workspace.question_count), (2, 3))

	def test_last_question_and_activity(self):
		workspace = self.annotated(self.workspace)

		self.assertEqual(workspace.last_question, "Third?")
		self.assertEqual(workspace.last_activity_at, self.answer.created_at)

	def test_a_workspace_without_messages_was_last_active_when_created(self):
		workspace = self.annotated(self.empty)

		self.assertEqual((workspace.paper_count, workspace.question_count, workspace.last_question), (0, 0, None))
		self.assertEqual(workspace.last_activity_at, self.empty.created_at)

	def test_trims_the_last_question(self):
		Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content="x" * 500)

		self.assertEqual(len(self.annotated(self.workspace).last_question), 200)

	def test_properties_match_without_the_annotation(self):
		annotated = self.annotated(self.workspace)

		with self.assertNumQueries(4):
			plain = Workspace.objects.get(pk=self.workspace.pk)
			values = (plain.paper_count, plain.question_count, plain.last_question)
		self.assertEqual(values, (annotated.paper_count, annotated.question_count, annotated.last_question))
		self.assertEqual(plain.last_activity_at, annotated.last_activity_at)

	def test_annotated_properties_need_no_queries(self):
		workspace = self.annotated(self.workspace)

		with self.assertNumQueries(0):
			_ = (workspace.paper_count, workspace.question_count, workspace.last_question, workspace.last_activity_at)

	def test_orders_by_last_activity(self):
		Message.objects.filter(pk=self.answer.pk).update(created_at=timezone.now() - timedelta(days=30))
		Message.objects.filter(workspace=self.workspace).update(created_at=timezone.now() - timedelta(days=30))

		ordered = Workspace.objects.with_activity().order_by("-_last_activity_at")

		self.assertEqual(list(ordered), [self.empty, self.workspace])


class TrackingUpdateQuerySetTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user = get_user_model().objects.create_user(email="ada@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=user, name="Retrieval")
		cls.topic = TrackedTopic.objects.create(workspace=cls.workspace, query="retrieval")
		cls.papers = [
			Paper.objects.create(
				source=PaperSource.ARXIV, external_id=str(index), title=f"Paper {index}", url=f"https://arxiv.org/abs/{index}",
			)
			for index in range(3)
		]
		now = timezone.now()
		cls.old, cls.new = (
			TrackingUpdate.objects.create(workspace=cls.workspace, paper=paper, topic=cls.topic)
			for paper in cls.papers[:2]
		)
		Workspace.objects.filter(pk=cls.workspace.pk).update(created_at=now - timedelta(days=10))
		TrackingUpdate.objects.filter(pk=cls.old.pk).update(created_at=now - timedelta(days=2))
		TrackingUpdate.objects.filter(pk=cls.new.pk).update(created_at=now)

	def test_every_update_is_unseen_until_the_workspace_is_seen(self):
		self.assertEqual(set(TrackingUpdate.objects.unseen()), {self.old, self.new})
		self.assertEqual(Workspace.objects.with_activity().get(pk=self.workspace.pk).unseen_update_count, 2)

	def test_only_updates_after_the_last_visit_are_unseen(self):
		Workspace.objects.filter(pk=self.workspace.pk).update(updates_seen_at=timezone.now() - timedelta(days=1))

		self.assertEqual(list(TrackingUpdate.objects.unseen()), [self.new])
		self.assertEqual(Workspace.objects.with_activity().get(pk=self.workspace.pk).unseen_update_count, 1)

	def test_notes_whether_the_paper_is_already_in_the_workspace(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.papers[0])

		in_workspace = {update.paper_id: update._in_workspace for update in TrackingUpdate.objects.with_in_workspace()}

		self.assertEqual(in_workspace, {self.papers[0].pk: True, self.papers[1].pk: False})

