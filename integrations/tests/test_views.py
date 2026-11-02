from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from iam.models import User
from integrations.models import ApiToken

LIST_URL = reverse("api-token-list")


class ApiTokenViewSetTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.other_user = User.objects.create_user(email="grace@example.com", password="password")

	def setUp(self):
		self.client.force_authenticate(self.user)

	def test_creating_a_token_shows_it_once(self):
		response = self.client.post(LIST_URL, {"name": "Claude Desktop"})

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(response.data["token"].startswith(response.data["prefix"]))
		self.assertEqual(ApiToken.objects.authenticate(response.data["token"]).user, self.user)
		listed = self.client.get(LIST_URL).data
		self.assertEqual([row["name"] for row in listed], ["Claude Desktop"])
		self.assertNotIn("token", listed[0])

	def test_the_owner_cannot_be_written(self):
		self.client.post(LIST_URL, {"name": "Claude Desktop", "user": self.other_user.pk})

		self.assertEqual(ApiToken.objects.get().user, self.user)

	def test_a_blank_name_is_a_400_on_name(self):
		response = self.client.post(LIST_URL, {"name": "  "})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("name", response.data)

	def test_lists_only_the_callers_tokens(self):
		ApiToken.objects.issue(self.user, "Mine")
		ApiToken.objects.issue(self.other_user, "Theirs")

		self.assertEqual([row["name"] for row in self.client.get(LIST_URL).data], ["Mine"])

	def test_revoking_a_token_stops_it_working(self):
		token = ApiToken.objects.issue(self.user, "Claude Desktop")

		response = self.client.delete(reverse("api-token-detail", args=[token.pk]))

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertIsNone(ApiToken.objects.authenticate(token.raw_token))

	def test_cannot_revoke_another_users_token(self):
		token = ApiToken.objects.issue(self.other_user, "Theirs")

		self.assertEqual(self.client.delete(reverse("api-token-detail", args=[token.pk])).status_code, 404)
		self.assertTrue(ApiToken.objects.filter(pk=token.pk).exists())

	def test_returns_the_mcp_server_url(self):
		with self.settings(MCP_PUBLIC_URL="https://mcp.indexr.example/mcp"):
			response = self.client.get(reverse("mcp-server"))

		self.assertEqual(response.data, {"url": "https://mcp.indexr.example/mcp"})

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.client.get(LIST_URL).status_code, status.HTTP_401_UNAUTHORIZED)
		self.assertEqual(self.client.get(reverse("mcp-server")).status_code, status.HTTP_401_UNAUTHORIZED)
