from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.core.management import CommandError, call_command
from django.test import TestCase
from mcp.client.client import Client

from enums.Paper import PaperSource
from enums.Workspace import AskStage, MessageRole
from iam.models import User
from integrations.mcp_server import ApiTokenVerifier, LocalUser, build_server
from integrations.models import ApiToken
from papers.models import Chunk, Paper
from papers.services import Answer
from workspaces.models import Message, Workspace
from workspaces.services import AskDone, AskService, AskStatus

TOOLS = {
	"search_papers", "list_workspaces", "create_workspace", "list_workspace_papers", "get_paper",
	"add_paper_to_workspace", "remove_paper_from_workspace", "ask", "track_topic", "untrack_topic", "list_updates",
}


class McpServerTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=cls.user, name="Efficient attention")
		paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1", title="Attention Is All You Need", url="https://arxiv.org/abs/1",
		)
		cls.chunk = Chunk.objects.create(paper=paper, heading="Attention", text="Heads attend jointly.", start_page=4,
										 end_page=4, chunk_index=0)

	def setUp(self):
		LocalUser.user_id = self.user.pk
		self.addCleanup(setattr, LocalUser, "user_id", None)

	def call(self, tool: str, arguments: dict, progress: list | None = None):
		async def session():
			async with Client(build_server()) as client:
				callback = None
				if progress is not None:
					async def callback(done, total, message):
						progress.append((done, message))
				return await client.call_tool(tool, arguments, progress_callback=callback)

		return async_to_sync(session)()

	def test_lists_every_tool(self):
		async def names():
			async with Client(build_server()) as client:
				return {tool.name for tool in (await client.list_tools()).tools}

		self.assertEqual(async_to_sync(names)(), TOOLS)

	def test_search_returns_cited_passages(self):
		result = self.call("search_papers", {"query": "attention"})

		self.assertFalse(result.is_error)
		[passage] = result.structured_content["result"]
		self.assertEqual(passage["citation"], "Attention Is All You Need, §Attention, p.4")

	def test_a_bad_call_is_a_friendly_tool_error(self):
		result = self.call("list_workspace_papers", {"workspace_id": "not-a-uuid"})

		self.assertTrue(result.is_error)
		self.assertIn("No workspace with that ID", result.content[0].text)

	def test_a_call_without_a_user_is_refused(self):
		LocalUser.user_id = None

		result = self.call("list_workspaces", {})

		self.assertTrue(result.is_error)
		self.assertIn("Not signed in", result.content[0].text)

	def answered(self, question: Message):
		yield AskStatus(AskStage.SEARCHING)
		yield AskStatus(AskStage.ANSWERING)
		yield AskDone(AskService.save_answer(question.workspace, Answer(
			content="Heads attend jointly [1].", citations={1: self.chunk}, is_insufficient_context=False,
		)))

	def test_ask_reports_progress_and_returns_the_cited_answer(self):
		progress = []
		with patch.object(AskService, "ask", side_effect=self.answered):
			result = self.call("ask", {"workspace_id": str(self.workspace.pk), "question": "How do heads work?"}, progress)

		self.assertFalse(result.is_error)
		answer = result.structured_content
		self.assertEqual((answer["role"], answer["content"]), (MessageRole.ASSISTANT, "Heads attend jointly [1]."))
		self.assertEqual(answer["citations"][0]["chunk"]["citation"], "Attention Is All You Need, §Attention, p.4")
		self.assertEqual([message for _, message in progress], ["Looking through papers", "Writing the answer"])
		self.assertTrue(Message.objects.filter(role=MessageRole.USER, content="How do heads work?").exists())

	def test_a_failed_ask_is_a_friendly_tool_error(self):
		def failing(question):
			yield AskStatus(AskStage.SEARCHING)
			raise RuntimeError("model overloaded")

		with patch.object(AskService, "ask", side_effect=failing), self.assertLogs("integrations.mcp_server", "ERROR"):
			result = self.call("ask", {"workspace_id": str(self.workspace.pk), "question": "Hello?"})

		self.assertTrue(result.is_error)
		self.assertIn("Something went wrong while generating the answer", result.content[0].text)


class ApiTokenVerifierTests(TestCase):

	def test_maps_a_valid_token_to_its_user(self):
		user = User.objects.create_user(email="ada@example.com", password="password")
		token = ApiToken.objects.issue(user, "Claude Desktop")

		access = async_to_sync(ApiTokenVerifier().verify_token)(token.raw_token)

		self.assertEqual(access.subject, str(user.pk))

	def test_rejects_an_unknown_token(self):
		self.assertIsNone(async_to_sync(ApiTokenVerifier().verify_token)("ixr_unknown"))


class McpCommandTests(TestCase):

	def test_refuses_to_start_locally_without_a_valid_token(self):
		with patch.dict("os.environ", {"INDEXR_ACCESS_TOKEN": "ixr_unknown"}), self.assertRaisesMessage(CommandError, "INDEXR_ACCESS_TOKEN"):
			call_command("mcp")
