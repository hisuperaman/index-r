from django.conf import settings
from django.db.models import Count, Exists, F, IntegerField, OuterRef, Subquery
from django.db.models import (
	CASCADE, RESTRICT, BooleanField, CharField, CheckConstraint, DateTimeField, ForeignKey, ManyToManyField,
	PositiveIntegerField, Q, TextField,
	UniqueConstraint,
)

from enums.Workspace import MessageCitationLookup, MessageRole, TrackingUpdateKind
from papers.models import Chunk, Paper
from server.models import BaseModel, PrimaryModel
from workspaces.querysets import COUNT, LAST_QUESTION_LENGTH, TrackingUpdateQuerySet, WorkspaceQuerySet


class Workspace(PrimaryModel):
	user = ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=CASCADE,
		related_name="workspaces",
	)
	name = CharField(max_length=255)
	papers_only = BooleanField(default=False)
	updates_seen_at = DateTimeField(blank=True, null=True)
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
		paper = OuterRef(Paper.fields.id)
		citations = MessageCitation.objects.filter(chunk__paper=paper, message__workspace=self).order_by()
		mentioned_at = MessageCitationLookup.message__created_at
		return Paper.objects.with_authors().filter(Exists(citations)).annotate(
			_mention_count=Subquery(
				citations.values(MessageCitationLookup.chunk__paper.value)
				.annotate(count=Count(MessageCitation.fields.id)).values(COUNT),
				output_field=IntegerField(),
			),
			_last_mentioned_at=Subquery(citations.order_by(mentioned_at.desc()).values(mentioned_at.value)[:1]),
			_in_workspace=Exists(WorkspacePaper.objects.filter(workspace=self, paper=paper)),
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
	def unseen_update_count(self) -> int:
		if hasattr(self, "_unseen_update_count"):
			return self._unseen_update_count
		return self.tracking_updates.unseen().count()

	@property
	def last_activity_at(self):
		if hasattr(self, "_last_activity_at"):
			return self._last_activity_at
		message = self.messages.order_by("-created_at").first()
		return message.created_at if message else self.created_at


class WorkspacePaper(BaseModel):
	"""A paper mentioned in a workspace."""
	workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name="workspace_papers")
	paper = ForeignKey(Paper, on_delete=RESTRICT, related_name="workspace_papers")
	tracked_at = DateTimeField(blank=True, null=True)

	class Meta:
		constraints = [
			UniqueConstraint(fields=["workspace", "paper"], name="unique_workspace_paper"),
		]

	def __str__(self):
		return f"{self.paper.title[:30]} in {self.workspace.name}"

	@property
	def is_tracked(self) -> bool:
		return self.tracked_at is not None


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
	chunk = ForeignKey(Chunk, on_delete=RESTRICT, related_name="message_citations")
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
	checked_at = DateTimeField(blank=True, null=True)

	class Meta:
		constraints = [
			UniqueConstraint(fields=["workspace", "query"], name="unique_workspace_tracked_topic"),
			CheckConstraint(condition=~Q(query=""), name="tracked_topic_query_not_blank"),
		]

	def __str__(self):
		return f"{self.query} in {self.workspace.name}"


class TrackingUpdate(PrimaryModel):
	"""Something tracking found for a workspace: a new paper on a topic, a new citation or a new version."""
	workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name="tracking_updates")
	paper = ForeignKey(Paper, on_delete=CASCADE, related_name="tracking_updates")
	topic = ForeignKey(TrackedTopic, on_delete=CASCADE, blank=True, null=True, related_name="updates")
	cited_paper = ForeignKey(Paper, on_delete=CASCADE, blank=True, null=True, related_name="citation_updates")

	objects = TrackingUpdateQuerySet.as_manager()

	class Meta:
		constraints = [
			CheckConstraint(
				condition=Q(topic__isnull=True) | Q(cited_paper__isnull=True), name="tracking_update_one_reason",
			),
			CheckConstraint(
				condition=Q(cited_paper__isnull=True) | ~Q(paper=F("cited_paper")), name="tracking_update_not_self_citation",
			),
			UniqueConstraint(
				fields=["workspace", "paper"], condition=Q(topic__isnull=False), name="unique_new_paper_update",
			),
			UniqueConstraint(
				fields=["workspace", "paper", "cited_paper"], condition=Q(cited_paper__isnull=False),
				name="unique_new_citation_update",
			),
		]

	def __str__(self):
		return f"{self.kind.label}: {self.paper.title[:30]} in {self.workspace.name}"

	@property
	def kind(self) -> TrackingUpdateKind:
		if self.topic_id:
			return TrackingUpdateKind.NEW_PAPER
		if self.cited_paper_id:
			return TrackingUpdateKind.NEW_CITATION
		return TrackingUpdateKind.NEW_VERSION
