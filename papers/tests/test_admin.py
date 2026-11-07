from django.test import TestCase
from django.urls import reverse

from enums.Paper import PaperSource
from iam.models import User
from papers.models import Paper


class PaperAdminTests(TestCase):

	def test_lists_and_filters_papers_for_an_admin(self):
		admin = User.objects.create_superuser(email="admin@example.com")
		Paper.objects.create(source=PaperSource.ARXIV, external_id="1", title="Public paper", url="https://a.b")
		Paper.objects.create(source=PaperSource.UPLOAD, external_id="u1", title="Private paper", owner=admin)
		self.client.force_login(admin)

		response = self.client.get(reverse("admin:papers_paper_changelist"), {"visibility": "private"})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Private paper")
		self.assertNotContains(response, "Public paper")
