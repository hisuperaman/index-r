from django.test import TestCase

from enums.Paper import PaperSource
from enums.Workspace import MessageRole
from iam.models import User
from integrations.exceptions import ToolInputError
from integrations.services import ResearchToolsService as Tools
from papers.models import Chunk, Paper
from workspaces.models import Message, Workspace, WorkspacePaper


class ResearchToolsServiceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.me = User.objects.create_user(email="ada@example.com", password="password")
		cls.someone = User.objects.create_user(email="grace@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=cls.me, name="Efficient attention")
		cls.their_workspace = Workspace.objects.create(user=cls.someone, name="Private topic")

		def paper(external_id, owner=None):
			created = Paper.objects.create(
				source=PaperSource.UPLOAD if owner else PaperSource.ARXIV, external_id=external_id, owner=owner,
				title=f"Attention paper {external_id}", url="" if owner else f"https://arxiv.org/abs/{external_id}",
			)
			Chunk.objects.create(paper=created, heading="Attention", text="Sparse attention heads.", start_page=1,
								 end_page=1, chunk_index=0)
			return created

		cls.public, cls.mine, cls.theirs = paper("1"), paper("2", cls.me), paper("3", cls.someone)

	def test_search_returns_the_corpus_and_my_uploads_only(self):
		results = Tools.search_papers(self.me.pk, "attention")

		self.assertEqual({row["paper"]["id"] for row in results}, {str(self.public.id), str(self.mine.id)})
		self.assertTrue(all("citation" in row for row in results))

	def test_search_rejects_a_blank_query_and_a_backwards_year_range(self):
		with self.assertRaises(ToolInputError):
			Tools.search_papers(self.me.pk, "  ")
		with self.assertRaisesMessage(ToolInputError, "Must not be before year_from"):
			Tools.search_papers(self.me.pk, "attention", year_from=2021, year_to=2019)

	def test_search_caps_the_limit(self):
		self.assertEqual(len(Tools.search_papers(self.me.pk, "attention", limit=1)), 1)

	def test_lists_only_my_workspaces(self):
		self.assertEqual([row["name"] for row in Tools.list_workspaces(self.me.pk)], ["Efficient attention"])
		self.assertEqual(Tools.list_workspaces(self.me.pk, search="nothing"), [])

	def test_creates_a_workspace_and_validates_the_name(self):
		created = Tools.create_workspace(self.me.pk, "Protein folding")

		self.assertEqual(Workspace.objects.get(pk=created["id"]).user, self.me)
		with self.assertRaises(ToolInputError):
			Tools.create_workspace(self.me.pk, " ")

	def test_another_users_workspace_is_unknown(self):
		for call in (
				lambda: Tools.list_workspace_papers(self.me.pk, str(self.their_workspace.pk)),
				lambda: Tools.start_question(self.me.pk, str(self.their_workspace.pk), "Hello?"),
				lambda: Tools.list_workspace_papers(self.me.pk, "not-a-uuid"),
		):
			with self.assertRaisesMessage(ToolInputError, "No workspace with that ID"):
				call()

	def test_get_paper_hides_another_users_upload(self):
		self.assertEqual(Tools.get_paper(self.me.pk, str(self.mine.pk))["title"], "Attention paper 2")
		with self.assertRaisesMessage(ToolInputError, "No paper with that ID"):
			Tools.get_paper(self.me.pk, str(self.theirs.pk))

	def test_adds_and_removes_papers_in_my_workspace(self):
		added = Tools.add_paper_to_workspace(self.me.pk, str(self.workspace.pk), str(self.public.pk))

		self.assertEqual(added["paper"]["id"], str(self.public.id))
		self.assertEqual([row["id"] for row in Tools.list_workspace_papers(self.me.pk, str(self.workspace.pk))],
						 [str(self.public.id)])
		Tools.remove_paper_from_workspace(self.me.pk, str(self.workspace.pk), str(self.public.pk))
		self.assertFalse(WorkspacePaper.objects.exists())
		with self.assertRaisesMessage(ToolInputError, "isn't in this workspace"):
			Tools.remove_paper_from_workspace(self.me.pk, str(self.workspace.pk), str(self.public.pk))

	def test_cannot_add_another_users_private_paper(self):
		with self.assertRaises(ToolInputError):
			Tools.add_paper_to_workspace(self.me.pk, str(self.workspace.pk), str(self.theirs.pk))
		self.assertFalse(WorkspacePaper.objects.exists())

	def test_starts_a_question_as_my_message(self):
		message = Tools.start_question(self.me.pk, str(self.workspace.pk), "How do sparse heads work?")

		self.assertEqual((message.workspace, message.role), (self.workspace, MessageRole.USER))
		with self.assertRaises(ToolInputError):
			Tools.start_question(self.me.pk, str(self.workspace.pk), "")

	def test_answer_includes_its_citations(self):
		message = Message.objects.create(workspace=self.workspace, role=MessageRole.ASSISTANT, content="A [1].")
		message.citations.create(chunk=self.public.chunks.get(), number=1)

		answer = Tools.answer(str(message.pk))

		self.assertEqual((answer["content"], answer["citations"][0]["number"]), ("A [1].", 1))
