from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from enums.Paper import PaperSource
from enums.Workspace import MessageRole
from iam.models import User
from papers.models import Paper
from workspaces.models import Message, Workspace, WorkspacePaper

LIST_URL = reverse("workspace-list")


def detail_url(workspace: Workspace) -> str:
	return reverse("workspace-detail", args=[workspace.pk])


class WorkspaceViewSetTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.other_user = User.objects.create_user(email="grace@example.com", password="password")

	def setUp(self):
		self.client.force_authenticate(self.user)

	def test_creates_a_workspace_owned_by_the_caller(self):
		response = self.client.post(LIST_URL, {"name": "  Sparse retrieval  "})

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		workspace = Workspace.objects.get()
		self.assertEqual((workspace.user, workspace.name), (self.user, "Sparse retrieval"))
		self.assertEqual(response.data["id"], str(workspace.id))

	def test_owner_and_timestamps_cannot_be_written(self):
		response = self.client.post(LIST_URL, {
			"name": "Sparse retrieval", "user": self.other_user.pk, "id": "00000000-0000-0000-0000-000000000000",
			"created_at": "2000-01-01T00:00:00Z",
		})

		workspace = Workspace.objects.get()
		self.assertEqual(workspace.user, self.user)
		self.assertNotEqual(str(workspace.id), "00000000-0000-0000-0000-000000000000")
		self.assertNotEqual(response.data["created_at"][:4], "2000")
		self.assertNotIn("user", response.data)

	def test_a_blank_name_is_a_400_on_name(self):
		response = self.client.post(LIST_URL, {"name": "   "})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("name", response.data)

	def test_lists_only_the_callers_workspaces_newest_first(self):
		older = Workspace.objects.create(user=self.user, name="Older")
		newer = Workspace.objects.create(user=self.user, name="Newer")
		Workspace.objects.create(user=self.other_user, name="Someone else's")

		response = self.client.get(LIST_URL)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual([row["id"] for row in response.data["results"]], [str(newer.id), str(older.id)])

	def test_orders_by_name_on_request(self):
		Workspace.objects.create(user=self.user, name="Beta")
		Workspace.objects.create(user=self.user, name="Alpha")

		response = self.client.get(LIST_URL, {"ordering": "name"})

		self.assertEqual([row["name"] for row in response.data["results"]], ["Alpha", "Beta"])

	def test_pages_through_the_list_with_a_cursor(self):
		for index in range(3):
			Workspace.objects.create(user=self.user, name=f"Workspace {index}")

		first = self.client.get(LIST_URL, {"page_size": 2})
		second = self.client.get(first.data["next"])

		self.assertEqual(len(first.data["results"]), 2)
		self.assertEqual(len(second.data["results"]), 1)
		self.assertIsNone(second.data["next"])

	def test_list_query_count_does_not_grow_with_rows(self):
		Workspace.objects.create(user=self.user, name="Workspace 0")
		with CaptureQueriesContext(connection) as one:
			self.client.get(LIST_URL)

		for index in range(1, 5):
			Workspace.objects.create(user=self.user, name=f"Workspace {index}")
		with CaptureQueriesContext(connection) as five:
			response = self.client.get(LIST_URL)

		self.assertEqual(len(response.data["results"]), 5)
		self.assertEqual(len(five), len(one))

	def test_renames_a_workspace(self):
		workspace = Workspace.objects.create(user=self.user, name="Old")

		response = self.client.patch(detail_url(workspace), {"name": "New"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		workspace.refresh_from_db()
		self.assertEqual(workspace.name, "New")

	def test_deletes_a_workspace(self):
		workspace = Workspace.objects.create(user=self.user, name="Retrieval")

		response = self.client.delete(detail_url(workspace))

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(Workspace.objects.exists())

	def test_another_users_workspace_is_not_found(self):
		workspace = Workspace.objects.create(user=self.other_user, name="Private")

		for response in (
			self.client.get(detail_url(workspace)),
			self.client.patch(detail_url(workspace), {"name": "Taken"}),
			self.client.delete(detail_url(workspace)),
		):
			self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		workspace.refresh_from_db()
		self.assertEqual(workspace.name, "Private")

	def test_a_superuser_sees_only_their_own_workspaces(self):
		superuser = User.objects.create_superuser(email="admin@example.com")
		workspace = Workspace.objects.create(user=self.user, name="Private")
		self.client.force_authenticate(superuser)

		self.assertEqual(self.client.get(LIST_URL).data["results"], [])
		self.assertEqual(self.client.get(detail_url(workspace)).status_code, status.HTTP_404_NOT_FOUND)

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.client.get(LIST_URL).status_code, status.HTTP_401_UNAUTHORIZED)


def create_paper(external_id: str) -> Paper:
	return Paper.objects.create(
		source=PaperSource.ARXIV, external_id=external_id, title=f"Paper {external_id}",
		url=f"https://arxiv.org/abs/{external_id}",
	)


class WorkspacePaperViewSetTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.other_user = User.objects.create_user(email="grace@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=cls.user, name="Retrieval")
		cls.paper = create_paper("1706.03762")

	def setUp(self):
		self.client.force_authenticate(self.user)

	def list_url(self, workspace: Workspace | None = None) -> str:
		return reverse("workspace-paper-list", args=[(workspace or self.workspace).pk])

	def detail_url(self, paper: Paper) -> str:
		return reverse("workspace-paper-detail", args=[self.workspace.pk, paper.pk])

	def test_adds_a_paper_to_the_workspace(self):
		response = self.client.post(self.list_url(), {"paper_id": self.paper.pk})

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertQuerySetEqual(self.workspace.papers.all(), [self.paper])
		self.assertEqual(response.data["paper"]["id"], str(self.paper.id))
		self.assertNotIn("paper_id", response.data)

	def test_adding_a_paper_twice_is_a_400_on_paper_id(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

		response = self.client.post(self.list_url(), {"paper_id": self.paper.pk})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("paper_id", response.data)

	def test_the_same_paper_can_be_in_another_workspace(self):
		other = Workspace.objects.create(user=self.user, name="Other")
		WorkspacePaper.objects.create(workspace=other, paper=self.paper)

		response = self.client.post(self.list_url(), {"paper_id": self.paper.pk})

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	def test_an_unknown_paper_is_a_400_on_paper_id(self):
		response = self.client.post(self.list_url(), {"paper_id": "00000000-0000-0000-0000-000000000000"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("paper_id", response.data)

	def test_lists_the_workspaces_papers_newest_first(self):
		older = create_paper("1")
		WorkspacePaper.objects.create(workspace=self.workspace, paper=older)
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)
		WorkspacePaper.objects.create(workspace=Workspace.objects.create(user=self.user, name="Other"), paper=older)

		response = self.client.get(self.list_url())

		self.assertEqual([row["paper"]["id"] for row in response.data["results"]], [str(self.paper.id), str(older.id)])

	def test_list_query_count_does_not_grow_with_rows(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)
		with CaptureQueriesContext(connection) as one:
			self.client.get(self.list_url())

		for index in range(4):
			WorkspacePaper.objects.create(workspace=self.workspace, paper=create_paper(str(index)))
		with CaptureQueriesContext(connection) as five:
			response = self.client.get(self.list_url())

		self.assertEqual(len(response.data["results"]), 5)
		self.assertEqual(len(five), len(one))

	def test_removes_a_paper_by_its_id(self):
		WorkspacePaper.objects.create(workspace=self.workspace, paper=self.paper)

		response = self.client.delete(self.detail_url(self.paper))

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(WorkspacePaper.objects.exists())
		self.assertTrue(Paper.objects.filter(pk=self.paper.pk).exists())

	def test_removing_a_paper_not_in_the_workspace_is_a_404(self):
		self.assertEqual(self.client.delete(self.detail_url(self.paper)).status_code, status.HTTP_404_NOT_FOUND)

	def test_another_users_workspace_is_not_found(self):
		other = Workspace.objects.create(user=self.other_user, name="Private")
		WorkspacePaper.objects.create(workspace=other, paper=self.paper)

		for response in (
			self.client.get(self.list_url(other)),
			self.client.post(self.list_url(other), {"paper_id": create_paper("2").pk}),
			self.client.delete(reverse("workspace-paper-detail", args=[other.pk, self.paper.pk])),
		):
			self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(WorkspacePaper.objects.filter(workspace=other).count(), 1)

	def test_a_malformed_workspace_id_is_a_404(self):
		self.assertEqual(
			self.client.get(reverse("workspace-paper-list", args=["not-a-uuid"])).status_code,
			status.HTTP_404_NOT_FOUND,
		)

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.client.get(self.list_url()).status_code, status.HTTP_401_UNAUTHORIZED)


class MessageViewSetTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.other_user = User.objects.create_user(email="grace@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=cls.user, name="Retrieval")

	def setUp(self):
		self.client.force_authenticate(self.user)

	def list_url(self, workspace: Workspace | None = None) -> str:
		return reverse("workspace-message-list", args=[(workspace or self.workspace).pk])

	def test_posts_a_user_message(self):
		response = self.client.post(self.list_url(), {"content": "Which models beat 0.9 F1 on MMLU?"})

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		message = Message.objects.get()
		self.assertEqual(
			(message.workspace, message.role, message.content),
			(self.workspace, MessageRole.USER, "Which models beat 0.9 F1 on MMLU?"),
		)
		self.assertEqual(response.data["role"], MessageRole.USER)

	def test_the_role_cannot_be_written(self):
		self.client.post(self.list_url(), {"content": "Hello", "role": MessageRole.ASSISTANT})

		self.assertEqual(Message.objects.get().role, MessageRole.USER)

	def test_blank_content_is_a_400_on_content(self):
		response = self.client.post(self.list_url(), {"content": "   "})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("content", response.data)

	def test_lists_the_workspaces_messages_newest_first(self):
		first = Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content="Question")
		second = Message.objects.create(workspace=self.workspace, role=MessageRole.ASSISTANT, content="Answer")
		Message.objects.create(
			workspace=Workspace.objects.create(user=self.user, name="Other"), role=MessageRole.USER, content="Elsewhere",
		)

		response = self.client.get(self.list_url())

		self.assertEqual([row["id"] for row in response.data["results"]], [str(second.id), str(first.id)])

	def test_list_query_count_does_not_grow_with_rows(self):
		Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content="0")
		with CaptureQueriesContext(connection) as one:
			self.client.get(self.list_url())

		for index in range(1, 5):
			Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content=str(index))
		with CaptureQueriesContext(connection) as five:
			response = self.client.get(self.list_url())

		self.assertEqual(len(response.data["results"]), 5)
		self.assertEqual(len(five), len(one))

	def test_messages_cannot_be_edited_or_deleted(self):
		message = Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content="Question")
		url = f"{self.list_url()}{message.pk}/"

		self.assertEqual(self.client.patch(url, {"content": "Edited"}).status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

	def test_another_users_workspace_is_not_found(self):
		other = Workspace.objects.create(user=self.other_user, name="Private")

		self.assertEqual(self.client.get(self.list_url(other)).status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(
			self.client.post(self.list_url(other), {"content": "Hello"}).status_code, status.HTTP_404_NOT_FOUND,
		)
		self.assertFalse(Message.objects.exists())

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.client.get(self.list_url()).status_code, status.HTTP_401_UNAUTHORIZED)
