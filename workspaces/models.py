from django.conf import settings
from django.db.models import (
	CASCADE, PROTECT, CharField, ForeignKey, ManyToManyField, TextField, UniqueConstraint,
)

from enums.Workspace import MessageRole
from papers.models import Paper
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

	def __str__(self):
		return f"{self.role} message in {self.workspace.name}"
