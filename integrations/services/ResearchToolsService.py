from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from functools import partial

from django.db import transaction
from django.db.models import Prefetch
from rest_framework.serializers import Serializer

from enums.Workspace import (
	MessageCitationLookup, MessageRole, WorkspaceLookup, WorkspacePaperLookup,
)
from iam.models import User
from iam.scoping import scope_to_user
from integrations.exceptions import ToolInputError
from papers.models import Chunk, Paper, PaperAuthor
from papers.serializers import ChunkSerializer, PaperSerializer
from workspaces.models import Message, MessageCitation, TrackedTopic, TrackingUpdate, Workspace, WorkspacePaper
from workspaces.serializers import (
	MessageSerializer, TrackedTopicSerializer, TrackingUpdateSerializer, WorkspacePaperSerializer, WorkspaceSerializer,
)
from workspaces.tasks import check_tracked_topic


def first_error(serializer: Serializer) -> str:
	"""The first validation message from `serializer`, for showing to the user."""
	messages = next(iter(serializer.errors.values()))
	return str(messages[0] if isinstance(messages, list) else messages)


class ResearchToolsService:
	"""The MCP tools, each acting as one user and seeing only what that user can."""

	SEARCH_LIMIT = 25
	LIST_LIMIT = 50

	@staticmethod
	def user(user_id: int) -> User:
		return User.objects.get(pk=user_id, is_active=True)

	@classmethod
	def workspace(cls, user: User, workspace_id: str) -> Workspace:
		"""The user's workspace with this ID, or a ToolInputError."""
		try:
			workspace = scope_to_user(Workspace.objects.with_activity(), user).filter(pk=workspace_id).first()
		except DjangoValidationError:
			workspace = None
		if workspace is None:
			raise ToolInputError("No workspace with that ID. Use list_workspaces to find one.")
		return workspace

	@classmethod
	def paper(cls, user: User, paper_id: str) -> Paper:
		"""A paper the user can see, or a ToolInputError."""
		try:
			paper = Paper.objects.visible_to(user).with_authors().filter(pk=paper_id).first()
		except DjangoValidationError:
			paper = None
		if paper is None:
			raise ToolInputError("No paper with that ID.")
		return paper

	@classmethod
	def search_papers(cls, user_id: int, query: str, year_from: int | None = None, year_to: int | None = None,
					  venue: str | None = None, min_citations: int | None = None, limit: int = 10) -> list[dict[str, Any]]:
		"""Passages matching `query` in the shared corpus and the user's uploads, best first."""
		user = cls.user(user_id)
		filters = {'q': query, 'year_from': year_from, 'year_to': year_to, 'venue': venue, 'min_citations': min_citations}
		serializer = ChunkSerializer(data={key: value for key, value in filters.items() if value not in (None, "")})
		if not serializer.is_valid():
			raise ToolInputError(first_error(serializer))
		data = serializer.validated_data
		chunks = (
			Chunk.objects.visible_to(user)
			.filter_papers(
				year_from=data.get('year_from'), year_to=data.get('year_to'), venue=data.get('venue'),
				min_citations=data.get('min_citations'),
			)
			.search(data['q'])
			.select_related(Chunk.fields.paper)[:max(1, min(limit, cls.SEARCH_LIMIT))]
		)
		return ChunkSerializer(chunks, many=True).data

	@classmethod
	def list_workspaces(cls, user_id: int, search: str | None = None) -> list[dict[str, Any]]:
		"""The user's workspaces, most recently active first."""
		workspaces = scope_to_user(Workspace.objects.with_activity(), cls.user(user_id))
		if search:
			workspaces = workspaces.filter(name__icontains=search)
		ordered = workspaces.order_by(WorkspaceLookup.last_activity_at.desc())[:cls.LIST_LIMIT]
		return WorkspaceSerializer(ordered, many=True).data

	@classmethod
	def create_workspace(cls, user_id: int, name: str) -> dict[str, Any]:
		"""Creates a workspace for the user."""
		serializer = WorkspaceSerializer(data={Workspace.fields.name: name})
		if not serializer.is_valid():
			raise ToolInputError(first_error(serializer))
		return WorkspaceSerializer(serializer.save(user=cls.user(user_id))).data

	@classmethod
	def list_workspace_papers(cls, user_id: int, workspace_id: str) -> list[dict[str, Any]]:
		"""The papers in one of the user's workspaces, newest first."""
		workspace = cls.workspace(cls.user(user_id), workspace_id)
		links = (
			WorkspacePaper.objects.filter(workspace=workspace)
			.select_related(WorkspacePaper.fields.paper)
			.prefetch_related(Prefetch(
				WorkspacePaperLookup.paper__paper_authors.value,
				queryset=PaperAuthor.objects.select_related(PaperAuthor.fields.author),
			))
			.order_by(WorkspacePaper.fields.created_at.desc())[:cls.LIST_LIMIT]
		)
		return [PaperSerializer(link.paper).data for link in links]

	@classmethod
	def get_paper(cls, user_id: int, paper_id: str) -> dict[str, Any]:
		"""Details of a paper the user can see."""
		return PaperSerializer(cls.paper(cls.user(user_id), paper_id)).data

	@classmethod
	def add_paper_to_workspace(cls, user_id: int, workspace_id: str, paper_id: str) -> dict[str, Any]:
		"""Adds a paper the user can see to one of their workspaces."""
		workspace = cls.workspace(cls.user(user_id), workspace_id)
		serializer = WorkspacePaperSerializer(data={'paper_id': paper_id}, workspace=workspace)
		if not serializer.is_valid():
			raise ToolInputError(first_error(serializer))
		return WorkspacePaperSerializer(serializer.save(workspace=workspace)).data

	@classmethod
	def remove_paper_from_workspace(cls, user_id: int, workspace_id: str, paper_id: str) -> dict[str, Any]:
		"""Removes a paper from one of the user's workspaces."""
		workspace = cls.workspace(cls.user(user_id), workspace_id)
		try:
			deleted, _ = WorkspacePaper.objects.filter(workspace=workspace, paper_id=paper_id).delete()
		except DjangoValidationError:
			deleted = 0
		if not deleted:
			raise ToolInputError("That paper isn't in this workspace.")
		return {'removed': True}

	@classmethod
	def track_topic(cls, user_id: int, workspace_id: str, query: str) -> dict[str, Any]:
		"""Starts tracking a topic in one of the user's workspaces and queues its first check."""
		workspace = cls.workspace(cls.user(user_id), workspace_id)
		serializer = TrackedTopicSerializer(data={TrackedTopic.fields.query: query}, workspace=workspace)
		if not serializer.is_valid():
			raise ToolInputError(first_error(serializer))
		topic = serializer.save(workspace=workspace)
		transaction.on_commit(partial(check_tracked_topic.delay, topic.pk), robust=True)
		return TrackedTopicSerializer(topic).data

	@classmethod
	def untrack_topic(cls, user_id: int, workspace_id: str, query: str) -> dict[str, Any]:
		"""Stops tracking a topic in one of the user's workspaces."""
		workspace = cls.workspace(cls.user(user_id), workspace_id)
		deleted, _ = TrackedTopic.objects.filter(workspace=workspace, query__iexact=query.strip()).delete()
		if not deleted:
			raise ToolInputError("This workspace doesn't track that topic. Use list_updates to see its topics.")
		return {'untracked': True}

	@classmethod
	def list_updates(cls, user_id: int, workspace_id: str, unseen_only: bool = False) -> dict[str, Any]:
		"""What tracking found in one of the user's workspaces, newest first, with the topics it tracks."""
		workspace = cls.workspace(cls.user(user_id), workspace_id)
		updates = TrackingUpdate.objects.filter(workspace=workspace).with_details()
		if unseen_only:
			updates = updates.unseen()
		return {
			'topics': TrackedTopicSerializer(workspace.tracked_topics.order_by(TrackedTopic.fields.created_at), many=True).data,
			'updates_seen_at': workspace.updates_seen_at,
			'updates': TrackingUpdateSerializer(
				updates.order_by(TrackingUpdate.fields.created_at.desc())[:cls.LIST_LIMIT], many=True,
			).data,
		}

	@classmethod
	def start_question(cls, user_id: int, workspace_id: str, question: str) -> Message:
		"""Saves `question` as the user's message in one of their workspaces."""
		workspace = cls.workspace(cls.user(user_id), workspace_id)
		serializer = MessageSerializer(data={Message.fields.content: question})
		if not serializer.is_valid():
			raise ToolInputError(first_error(serializer))
		return serializer.save(workspace=workspace, role=MessageRole.USER)

	@staticmethod
	def answer(message_id: str) -> dict[str, Any]:
		"""The saved answer with its citations."""
		message = Message.objects.prefetch_related(Prefetch(
			Message.fields.citations,
			queryset=MessageCitation.objects.select_related(MessageCitationLookup.chunk__paper.value),
		)).get(pk=message_id)
		return MessageSerializer(message).data
