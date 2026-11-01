from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from iam.models import User
from workspaces.models import Workspace

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
