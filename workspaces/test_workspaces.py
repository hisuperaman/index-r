from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Workspace
from .permissions import OWNER_FIELD

User = get_user_model()
LIST = "/api/workspaces/"


def make_workspace(owner, name):
    return Workspace.objects.create(**{OWNER_FIELD: owner, "name": name})


class WorkspaceAPITests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw")
        self.bob = User.objects.create_user("bob", password="pw")
        self.a_ws = make_workspace(self.alice, "Alice topic")
        self.b_ws = make_workspace(self.bob, "Bob topic")
        self.client.force_authenticate(self.alice)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(LIST).status_code, 401)
        self.assertEqual(self.client.post(LIST, {"name": "x"}).status_code, 401)

    def test_list_only_returns_own(self):
        res = self.client.get(LIST)
        self.assertEqual(res.status_code, 200)
        results = res.data["results"] if isinstance(res.data, dict) else res.data
        self.assertEqual([w["name"] for w in results], ["Alice topic"])

    def test_create_assigns_owner_and_ignores_payload_owner(self):
        res = self.client.post(LIST, {"name": "New", OWNER_FIELD: self.bob.pk})
        self.assertEqual(res.status_code, 201)
        created = Workspace.objects.get(name="New")
        self.assertEqual(getattr(created, OWNER_FIELD), self.alice)
        self.assertNotIn(OWNER_FIELD, res.data)

    def test_cannot_retrieve_update_or_delete_others(self):
        url = f"{LIST}{self.b_ws.pk}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {"name": "hack"}).status_code, 404)
        self.assertEqual(self.client.put(url, {"name": "hack"}).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.b_ws.refresh_from_db()
        self.assertEqual(self.b_ws.name, "Bob topic")

    def test_update_and_delete_own(self):
        url = f"{LIST}{self.a_ws.pk}/"
        self.assertEqual(self.client.patch(url, {"name": "Renamed"}).status_code, 200)
        self.a_ws.refresh_from_db()
        self.assertEqual(self.a_ws.name, "Renamed")
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Workspace.objects.filter(pk=self.a_ws.pk).exists())


