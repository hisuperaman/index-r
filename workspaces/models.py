from django.conf import settings
from django.db.models import CASCADE, CharField, ForeignKey, TextField

from enums.Workspace import Role
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


class Message(PrimaryModel):
    workspace = ForeignKey(
        Workspace,
        on_delete=CASCADE,
        related_name="messages",
    )
    role = CharField(
        max_length=20,
        choices=Role,
    )
    content = TextField()

    def __str__(self):
        return f"{self.role} message in {self.workspace.name}"