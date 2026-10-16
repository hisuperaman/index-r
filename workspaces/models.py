from django.conf import settings
from django.db.models import CASCADE, CharField, FileField, ForeignKey, TextField

from enums.Workspace import MessageRole
from server.models import PrimaryModel


class Workspace(PrimaryModel):
	user = ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=CASCADE,
		related_name="workspaces",
	)
	name = CharField(max_length=255)

	def __str__(self):
		return self.name


class Paper(PrimaryModel):
    workspace = ForeignKey(
        Workspace,
        on_delete=CASCADE,
        related_name="papers",
    )
    title = CharField(max_length=255)
    file = FileField(upload_to="papers/")

    def __str__(self):
        return self.title


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
