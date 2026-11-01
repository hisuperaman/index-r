from django.conf import settings
from django.db.models import Count, Exists, IntegerField, OuterRef, Subquery
from django.db.models import (
	CASCADE, PROTECT, BooleanField, CharField, CheckConstraint, ForeignKey, ManyToManyField, PositiveIntegerField, Q, TextField,
	UniqueConstraint,
)

from enums.Workspace import MessageRole
from papers.models import Chunk, Paper
from server.models import BaseModel, PrimaryModel
from workspaces.querysets import LAST_QUESTION_LENGTH, WorkspaceQuerySet


class Workspace(PrimaryModel):
	user = ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=CASCADE,
		related_name="workspaces",
	)
	name = CharField(max_length=255)
	papers_only = BooleanField(default=False)
	papers = ManyToManyField(
		Paper,
		through="WorkspacePaper",
		related_name="workspaces",
	)

	objects = WorkspaceQuerySet.as_manager()

	class Meta:
		constraints = [
			CheckConstraint(condition=~Q(name=""), name="workspace_name_not_blank"),
		]

	def __str__(self):
		return self.name

	def mentioned_papers(self):
		"""Papers this workspace's answers cite, annotated with how often and when last, and whether they're in it."""
		citations = MessageCitation.objects.filter(chunk__paper=OuterRef("pk"), message__workspace=self).order_by()
		return Paper.objects.with_authors().filter(Exists(citations)).annotate(
			_mention_count=Subquery(
				citations.values("chunk__paper").annotate(count=Count("pk")).values("count"), output_field=IntegerField(),
			),
			_last_mentioned_at=Subquery(citations.order_by("-message__created_at").values("message__created_at")[:1]),
			_in_workspace=Exists(WorkspacePaper.objects.filter(workspace=self, paper=OuterRef("pk"))),
		)

	@property
	def paper_count(self) -> int:
		if hasattr(self, "_paper_count"):
			return self._paper_count
		return self.workspace_papers.count()

	@property
	def question_count(self) -> int:
		if hasattr(self, "_question_count"):
			return self._question_count
		return self.messages.filter(role=MessageRole.USER).count()

	@property
	def last_question(self) -> str | None:
		if hasattr(self, "_last_question"):
			return self._last_question
		question = self.messages.filter(role=MessageRole.USER).order_by("-created_at").first()
		return question.content[:LAST_QUESTION_LENGTH] if question else None

	@property
	def last_activity_at(self):
		if hasattr(self, "_last_activity_at"):
			return self._last_activity_at
		message = self.messages.order_by("-created_at").first()
		return message.created_at if message else self.created_at


class WorkspacePaper(BaseModel):
	"""A paper mentioned in a workspace."""
	workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name="workspace_papers")
	paper = ForeignKey(Paper, on_delete=PROTECT, related_name="workspace_papers")

	class Meta:
		constraints = [
			UniqueConstraint(fields=["workspace", "paper"], name="unique_workspace_paper"),
		]

	def __str__(self):
		return f"{self.paper.title[:30]} in {self.workspace.name}"


class Message(PrimaryModel):
	workspace = ForeignKey(
		Workspace,
		on_delete=CASCADE,
		related_name="messages",
	)
	role = CharField(
		max_length=20,
		choices=MessageRole,
	)
	content = TextField()
	cited_chunks = ManyToManyField(Chunk, through="MessageCitation", related_name="citing_messages")

	class Meta:
		constraints = [
			CheckConstraint(condition=~Q(content=""), name="message_content_not_blank"),
			CheckConstraint(condition=Q(role__in=MessageRole.values), name="message_role_valid"),
		]

	def __str__(self):
		return f"{self.role} message in {self.workspace.name}"


class MessageCitation(BaseModel):
	"""A chunk an assistant message cites as [number]."""
	message = ForeignKey(Message, on_delete=CASCADE, related_name="citations")
	chunk = ForeignKey(Chunk, on_delete=PROTECT, related_name="message_citations")
	number = PositiveIntegerField()

	class Meta:
		ordering = ["number"]
		constraints = [
			UniqueConstraint(fields=["message", "number"], name="unique_message_citation_number"),
			UniqueConstraint(fields=["message", "chunk"], name="unique_message_citation_chunk"),
			CheckConstraint(condition=Q(number__gte=1), name="message_citation_number_positive"),
		]

	def __str__(self):
		return f"[{self.number}] in message {self.message_id}"


class TrackedTopic(PrimaryModel):
	"""A query a workspace re-runs to find papers published since it last looked."""
	workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name="tracked_topics")
	query = CharField(max_length=255)

	class Meta:
		constraints = [
			UniqueConstraint(fields=["workspace", "query"], name="unique_workspace_tracked_topic"),
			CheckConstraint(condition=~Q(query=""), name="tracked_topic_query_not_blank"),
		]

	def __str__(self):
		return f"{self.query} in {self.workspace.name}"
