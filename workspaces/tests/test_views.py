import json
from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase

from enums.Paper import PaperSource
from enums.Workspace import AskStage, MessageRole
from iam.models import User
from papers.models import Author, Chunk, Paper, PaperAuthor
from papers.services import Answer
from workspaces.models import Message, MessageCitation, Workspace, WorkspacePaper
from workspaces.services import AskDelta, AskDone, AskService, AskStatus

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

	def test_lists_activity_with_each_workspace(self):
		workspace = Workspace.objects.create(user=self.user, name="Retrieval")
		WorkspacePaper.objects.create(workspace=workspace, paper=create_paper("1"))
		Message.objects.create(workspace=workspace, role=MessageRole.USER, content="Which models beat 0.9 F1?")

		[row] = self.client.get(LIST_URL).data["results"]

		self.assertEqual(
			(row["paper_count"], row["question_count"], row["last_question"]), (1, 1, "Which models beat 0.9 F1?"),
		)
		self.assertIsNotNone(row["last_activity_at"])

	def test_lists_the_most_recently_active_first(self):
		quiet = Workspace.objects.create(user=self.user, name="Quiet")
		busy = Workspace.objects.create(user=self.user, name="Busy")
		Message.objects.create(workspace=quiet, role=MessageRole.USER, content="New question")

		response = self.client.get(LIST_URL)

		self.assertEqual([row["id"] for row in response.data["results"]], [str(quiet.id), str(busy.id)])

	def test_searches_by_name(self):
		Workspace.objects.create(user=self.user, name="Sparse retrieval")
		Workspace.objects.create(user=self.user, name="Protein folding")

		response = self.client.get(LIST_URL, {"search": "retriev"})

		self.assertEqual([row["name"] for row in response.data["results"]], ["Sparse retrieval"])

	def test_a_new_workspace_reports_empty_activity(self):
		response = self.client.post(LIST_URL, {"name": "Retrieval"})

		self.assertEqual(
			(response.data["paper_count"], response.data["question_count"], response.data["last_question"]), (0, 0, None),
		)

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
		def add(index: int) -> None:
			workspace = Workspace.objects.create(user=self.user, name=f"Workspace {index}")
			WorkspacePaper.objects.create(workspace=workspace, paper=create_paper(str(index)))
			Message.objects.create(workspace=workspace, role=MessageRole.USER, content="Question?")

		add(0)
		with CaptureQueriesContext(connection) as one:
			self.client.get(LIST_URL)

		for index in range(1, 5):
			add(index)
		with CaptureQueriesContext(connection) as five:
			response = self.client.get(LIST_URL)

		self.assertEqual(len(response.data["results"]), 5)
		self.assertEqual(len(five), len(one))

	def test_turns_on_answering_only_from_the_workspaces_papers(self):
		workspace = Workspace.objects.create(user=self.user, name="Retrieval")

		response = self.client.patch(detail_url(workspace), {"papers_only": True})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["papers_only"])
		workspace.refresh_from_db()
		self.assertTrue(workspace.papers_only)

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

	def test_cannot_add_another_users_private_paper(self):
		theirs = Paper.objects.create(
			source=PaperSource.UPLOAD, external_id="u2", title="Their notes", owner=self.other_user,
		)

		response = self.client.post(self.list_url(), {"paper_id": theirs.pk})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("paper_id", response.data)
		self.assertFalse(WorkspacePaper.objects.exists())

	def test_adds_my_own_private_paper(self):
		mine = Paper.objects.create(source=PaperSource.UPLOAD, external_id="u1", title="My notes", owner=self.user)

		response = self.client.post(self.list_url(), {"paper_id": mine.pk})

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(response.data["paper"]["is_private"])

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
			paper = create_paper(str(index))
			PaperAuthor.objects.create(paper=paper, author=Author.objects.create(name=f"Author {index}"), order=1)
			WorkspacePaper.objects.create(workspace=self.workspace, paper=paper)
		with CaptureQueriesContext(connection) as five:
			response = self.client.get(self.list_url())

		self.assertEqual(len(response.data["results"]), 5)
		self.assertEqual(response.data["results"][0]["paper"]["authors"], ["Author 3"])
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


class MentionedPaperViewSetTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=cls.user, name="Retrieval")

	def setUp(self):
		self.client.force_authenticate(self.user)

	def url(self, workspace: Workspace | None = None) -> str:
		return reverse("workspace-mentioned-paper-list", args=[(workspace or self.workspace).pk])

	def cite(self, external_id: str, authors: tuple[str, ...] = ()) -> Paper:
		paper = create_paper(external_id)
		for order, name in enumerate(authors, start=1):
			PaperAuthor.objects.create(paper=paper, author=Author.objects.create(name=name), order=order)
		chunk = Chunk.objects.create(paper=paper, text="Text.", start_page=1, end_page=1, chunk_index=0)
		message = Message.objects.create(workspace=self.workspace, role=MessageRole.ASSISTANT, content="A [1].")
		MessageCitation.objects.create(message=message, chunk=chunk, number=1)
		return paper

	def test_lists_cited_papers_most_recently_mentioned_first(self):
		older = self.cite("1", authors=("Ashish Vaswani",))
		newer = self.cite("2")
		WorkspacePaper.objects.create(workspace=self.workspace, paper=older)

		rows = self.client.get(self.url()).data["results"]

		self.assertEqual([row["id"] for row in rows], [str(newer.id), str(older.id)])
		self.assertEqual(
			(rows[1]["mention_count"], rows[1]["in_workspace"], rows[1]["authors"]), (1, True, ["Ashish Vaswani"]),
		)
		self.assertFalse(rows[0]["in_workspace"])
		self.assertIsNotNone(rows[0]["last_mentioned_at"])

	def test_query_count_does_not_grow_with_papers(self):
		self.cite("0", authors=("A",))
		with CaptureQueriesContext(connection) as one:
			self.client.get(self.url())

		for index in range(1, 5):
			self.cite(str(index), authors=("A", "B"))
		with CaptureQueriesContext(connection) as five:
			response = self.client.get(self.url())

		self.assertEqual(len(response.data["results"]), 5)
		self.assertEqual(len(five), len(one))

	def test_another_users_workspace_is_not_found(self):
		other = Workspace.objects.create(user=User.objects.create_user(email="grace@example.com"), name="Private")

		self.assertEqual(self.client.get(self.url(other)).status_code, status.HTTP_404_NOT_FOUND)

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_401_UNAUTHORIZED)


class MessageViewSetTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.other_user = User.objects.create_user(email="grace@example.com", password="password")
		cls.workspace = Workspace.objects.create(user=cls.user, name="Retrieval")
		cls.paper = create_paper("1706.03762")
		cls.chunk = Chunk.objects.create(
			paper=cls.paper, heading="Multi-Head Attention", text="Heads attend jointly.", start_page=4, end_page=4,
			chunk_index=0,
		)

	def setUp(self):
		self.client.force_authenticate(self.user)

	def list_url(self, workspace: Workspace | None = None) -> str:
		return reverse("workspace-message-list", args=[(workspace or self.workspace).pk])

	def stream_url(self, workspace: Workspace | None = None) -> str:
		return reverse("workspace-message-stream", args=[(workspace or self.workspace).pk])

	def answered(self, question: Message):
		yield AskStatus(AskStage.SEARCHING)
		yield AskDelta("Heads attend jointly [1].")
		yield AskDone(AskService.save_answer(question.workspace, Answer(
			content="Heads attend jointly [1].", citations={1: self.chunk}, is_insufficient_context=False,
		)))

	def failing(self, question: Message):
		yield AskStatus(AskStage.SEARCHING)
		raise RuntimeError("Cohere is down")

	def post(self, url: str, data: dict, ask=None, **headers):
		with patch.object(AskService, "ask", side_effect=ask or self.answered) as mock:
			response = self.client.post(url, data, **headers)
			if response.streaming:
				response.events = self.read_events(response)
		self.ask = mock
		return response

	@staticmethod
	def read_events(response) -> list[tuple[str, dict]]:
		body = b"".join(response.streaming_content).decode()
		events = []
		for block in filter(None, body.split("\n\n")):
			name, data = block.split("\n")
			events.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
		return events

	def test_answers_a_question_with_the_cited_assistant_message(self):
		response = self.post(self.list_url(), {"content": "How does multi-head attention work?"})

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["role"], MessageRole.ASSISTANT)
		self.assertEqual(response.data["content"], "Heads attend jointly [1].")
		[citation] = response.data["citations"]
		self.assertEqual(citation["number"], 1)
		self.assertEqual(citation["chunk"]["citation"], "Paper 1706.03762, §Multi-Head Attention, p.4")
		self.assertEqual(citation["chunk"]["paper"]["id"], str(self.paper.id))

	def test_saves_the_question_as_the_callers_message(self):
		self.post(self.list_url(), {"content": "How does multi-head attention work?", "role": MessageRole.ASSISTANT})

		question = Message.objects.get(role=MessageRole.USER)
		self.assertEqual((question.workspace, question.content), (self.workspace, "How does multi-head attention work?"))
		self.ask.assert_called_once_with(question)

	def test_blank_content_is_a_400_on_content(self):
		response = self.post(self.list_url(), {"content": "   "})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("content", response.data)
		self.ask.assert_not_called()

	def test_streams_status_deltas_and_the_final_message(self):
		response = self.post(self.stream_url(), {"content": "How does multi-head attention work?"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response["Content-Type"], "text/event-stream")
		self.assertEqual(response["Cache-Control"], "no-cache")
		self.assertEqual([name for name, _ in response.events], ["question", "status", "delta", "message"])
		question = response.events[0][1]
		self.assertEqual((question["role"], question["content"]), (MessageRole.USER, "How does multi-head attention work?"))
		self.assertEqual(question["id"], str(Message.objects.get(role=MessageRole.USER).id))
		self.assertEqual(response.events[1][1], {"stage": "searching", "label": "Looking through papers"})
		self.assertEqual(response.events[2][1], {"content": "Heads attend jointly [1]."})
		message = response.events[3][1]
		self.assertEqual((message["role"], message["citations"][0]["number"]), (MessageRole.ASSISTANT, 1))

	def test_streams_for_a_client_that_only_accepts_event_streams(self):
		response = self.post(self.stream_url(), {"content": "Hello?"}, HTTP_ACCEPT="text/event-stream")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.events[-1][0], "message")

	def test_a_failed_stream_ends_with_an_error_event(self):
		with self.assertLogs("workspaces.views", "ERROR"):
			response = self.post(self.stream_url(), {"content": "Hello?"}, ask=self.failing)

		self.assertEqual([name for name, _ in response.events], ["question", "status", "error"])
		self.assertIn("detail", response.events[-1][1])

	def test_a_blank_streamed_question_is_a_400_on_content(self):
		response = self.post(self.stream_url(), {"content": ""}, HTTP_ACCEPT="text/event-stream")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("content", json.loads(response.content))
		self.ask.assert_not_called()

	def test_asking_runs_outside_the_request_transaction(self):
		for url in (self.list_url(), self.stream_url()):
			self.assertEqual(resolve(url).func._non_atomic_requests, {"default"})

	def test_lists_the_workspaces_messages_newest_first(self):
		first = Message.objects.create(workspace=self.workspace, role=MessageRole.USER, content="Question")
		second = Message.objects.create(workspace=self.workspace, role=MessageRole.ASSISTANT, content="Answer")
		Message.objects.create(
			workspace=Workspace.objects.create(user=self.user, name="Other"), role=MessageRole.USER, content="Elsewhere",
		)

		response = self.client.get(self.list_url())

		self.assertEqual([row["id"] for row in response.data["results"]], [str(second.id), str(first.id)])

	def test_list_query_count_does_not_grow_with_rows_or_citations(self):
		def add_answer():
			message = Message.objects.create(workspace=self.workspace, role=MessageRole.ASSISTANT, content="A [1].")
			MessageCitation.objects.create(message=message, chunk=self.chunk, number=1)

		add_answer()
		with CaptureQueriesContext(connection) as one:
			self.client.get(self.list_url())

		for _ in range(4):
			add_answer()
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

	def test_cannot_ask_in_another_users_workspace(self):
		other = Workspace.objects.create(user=self.other_user, name="Private")

		self.assertEqual(self.post(self.list_url(other), {"content": "Hello"}).status_code, status.HTTP_404_NOT_FOUND)
		self.ask.assert_not_called()

	def test_cannot_stream_in_another_users_workspace(self):
		other = Workspace.objects.create(user=self.other_user, name="Private")

		self.assertEqual(self.post(self.stream_url(other), {"content": "Hello"}).status_code, status.HTTP_404_NOT_FOUND)
		self.ask.assert_not_called()

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.client.get(self.list_url()).status_code, status.HTTP_401_UNAUTHORIZED)
		self.assertEqual(self.post(self.stream_url(), {"content": "Hello"}).status_code, status.HTTP_401_UNAUTHORIZED)


class MessageAskFailureTests(APITransactionTestCase):
	"""Runs without a test transaction, as asking does in production."""

	def setUp(self):
		user = User.objects.create_user(email="ada@example.com", password="password")
		self.workspace = Workspace.objects.create(user=user, name="Retrieval")
		self.client.force_authenticate(user)

	def test_a_failed_answer_is_a_503_and_keeps_the_question(self):
		def failing(question):
			yield AskStatus(AskStage.SEARCHING)
			raise RuntimeError("Cohere is down")

		with patch.object(AskService, "ask", side_effect=failing), self.assertLogs("workspaces.views", "ERROR"):
			response = self.client.post(
				reverse("workspace-message-list", args=[self.workspace.pk]), {"content": "Hello?"},
			)

		self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
		self.assertQuerySetEqual(Message.objects.values_list("role", "content"), [(MessageRole.USER, "Hello?")])
