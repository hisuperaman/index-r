import json
import logging
from collections.abc import Iterator

from django.db import transaction
from django.db.models import Prefetch
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, ListModelMixin
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from enums.Paper import PaperLookup
from enums.Workspace import MessageCitationLookup, MessageRole, WorkspaceLookup, WorkspacePaperLookup
from iam.mixins import UserScopedMixin
from iam.permissions import IsOwner
from papers.models import PaperAuthor
from server.filters import OrderingFilter
from server.renderers import EventStreamRenderer
from workspaces.exceptions import AnswerUnavailable
from workspaces.mixins import WorkspaceScopedMixin
from workspaces.models import Message, MessageCitation, Workspace, WorkspacePaper
from workspaces.serializers import (
	MentionedPaperSerializer, MessageSerializer, WorkspacePaperSerializer, WorkspaceSerializer,
)
from workspaces.services import AskDelta, AskDone, AskEvent, AskService, AskStatus

logger = logging.getLogger(__name__)


class WorkspaceViewSet(UserScopedMixin, ModelViewSet):
	"""Creates, lists, renames and deletes the caller's own workspaces, most recently active first."""
	queryset = Workspace.objects.with_activity()
	serializer_class = WorkspaceSerializer
	permission_classes = [IsOwner]
	filter_backends = [SearchFilter, OrderingFilter]
	search_fields = [Workspace.fields.name]
	ordering_fields = [Workspace.fields.name, Workspace.fields.created_at, Workspace.fields.updated_at]
	ordering = [WorkspaceLookup.last_activity_at.desc()]


class WorkspacePaperViewSet(WorkspaceScopedMixin, ListModelMixin, CreateModelMixin, DestroyModelMixin, GenericViewSet):
	"""Lists, adds and removes the papers in one of the caller's workspaces."""
	queryset = WorkspacePaper.objects.select_related(WorkspacePaper.fields.paper).prefetch_related(
		Prefetch(
			WorkspacePaperLookup.paper__paper_authors.value,
			queryset=PaperAuthor.objects.select_related(PaperAuthor.fields.author),
		),
	)
	serializer_class = WorkspacePaperSerializer
	lookup_field = WorkspacePaper.fields.paper
	ordering_fields = [WorkspacePaper.fields.created_at]
	ordering = [WorkspacePaper.fields.created_at.desc()]

	def get_serializer(self, *args, **kwargs):
		return super().get_serializer(*args, workspace=self.workspace, **kwargs)


class MentionedPaperViewSet(WorkspaceScopedMixin, ListModelMixin, GenericViewSet):
	"""Lists the papers cited by answers in one of the caller's workspaces, most recently cited first."""
	serializer_class = MentionedPaperSerializer
	ordering = [PaperLookup.last_mentioned_at.desc()]

	def get_queryset(self):
		return self.workspace.mentioned_papers()


@method_decorator(transaction.non_atomic_requests, name='dispatch')
class MessageViewSet(WorkspaceScopedMixin, ListModelMixin, CreateModelMixin, GenericViewSet):
	"""Lists the chat in one of the caller's workspaces and answers the questions posted to it."""
	queryset = Message.objects.prefetch_related(Prefetch(
		Message.fields.citations,
		queryset=MessageCitation.objects.select_related(MessageCitationLookup.chunk__paper.value),
	))
	serializer_class = MessageSerializer
	ordering_fields = [Message.fields.created_at]
	ordering = [Message.fields.created_at.desc()]

	def create(self, request, *args, **kwargs):
		question = self.save_question()
		try:
			answer = next(event.message for event in AskService.ask(question) if isinstance(event, AskDone))
		except Exception as error:
			logger.exception("Answering message %s failed", question.pk)
			raise AnswerUnavailable() from error
		return Response(self.get_serializer(self.get_queryset().get(pk=answer.pk)).data, status=status.HTTP_201_CREATED)

	@action(detail=False, methods=['post'], renderer_classes=[JSONRenderer, EventStreamRenderer])
	def stream(self, request, *args, **kwargs):
		question = self.save_question()
		response = StreamingHttpResponse(self.event_stream(question), content_type='text/event-stream')
		response['Cache-Control'] = 'no-cache'
		response['X-Accel-Buffering'] = 'no'
		return response

	def save_question(self) -> Message:
		"""Validates the posted content and saves it as the caller's question."""
		serializer = self.get_serializer(data=self.request.data)
		serializer.is_valid(raise_exception=True)
		return serializer.save(workspace=self.workspace, role=MessageRole.USER)

	def event_stream(self, question: Message) -> Iterator[str]:
		"""Formats the ask's events as server-sent events, ending with an error event if it fails."""
		yield self.format_event('question', self.get_serializer(question).data)
		try:
			for event in AskService.ask(question):
				yield self.format_event(*self.to_event(event))
		except Exception:
			logger.exception("Answering message %s failed", question.pk)
			yield self.format_event('error', {'detail': AnswerUnavailable.default_detail})

	def to_event(self, event: AskEvent) -> tuple[str, dict]:
		"""The SSE event name and data for one ask event."""
		match event:
			case AskStatus(stage):
				return 'status', {'stage': stage, 'label': stage.label}
			case AskDelta(content):
				return 'delta', {'content': content}
			case AskDone(message):
				return 'message', self.get_serializer(self.get_queryset().get(pk=message.pk)).data

	@staticmethod
	def format_event(name: str, data: dict) -> str:
		return f"event: {name}\ndata: {json.dumps(data, cls=JSONEncoder)}\n\n"
