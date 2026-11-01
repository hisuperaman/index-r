from django.conf import settings
from django.db.models import (
	CASCADE, PROTECT, CharField, CheckConstraint, ForeignKey, ManyToManyField, PositiveIntegerField, Q, TextField,
	UniqueConstraint,
)

from enums.Workspace import MessageRole
from papers.models import Chunk, Paper
from server.models import BaseModel, PrimaryModel


class Workspace(PrimaryModel):
	user = ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=CASCADE,
		related_name="workspaces",
	)
	name = CharField(max_length=255)
	papers = ManyToManyField(
		Paper,
		through="WorkspacePaper",
		related_name="workspaces",
	)

	class Meta:
		constraints = [
			CheckConstraint(condition=~Q(name=""), name="workspace_name_not_blank"),
		]

	def __str__(self):
		return self.name


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
