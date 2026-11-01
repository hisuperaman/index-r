from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from papers.models import Paper
from papers.serializers import PaperSerializer
from workspaces.models import Message, Workspace, WorkspacePaper


class WorkspaceSerializer(ModelSerializer):
	class Meta:
		model = Workspace
		fields = [Workspace.fields.id, Workspace.fields.name, Workspace.fields.created_at, Workspace.fields.updated_at]
		read_only_fields = [Workspace.fields.id, Workspace.fields.created_at, Workspace.fields.updated_at]


class WorkspacePaperSerializer(ModelSerializer):
	paper = PaperSerializer(read_only=True)
	paper_id = PrimaryKeyRelatedField(source=WorkspacePaper.fields.paper, queryset=Paper.objects.all(), write_only=True)

	class Meta:
		model = WorkspacePaper
		read_only_fields = [WorkspacePaper.fields.paper, WorkspacePaper.fields.created_at]
		fields = [*read_only_fields, 'paper_id']

	def __init__(self, *args, workspace: Workspace | None = None, **kwargs):
		super().__init__(*args, **kwargs)
		self.workspace = workspace

	def validate(self, data):
		data = super().validate(data)
		if WorkspacePaper.objects.filter(workspace=self.workspace, paper=data['paper']).exists():
			raise ValidationError({'paper_id': ["This paper is already in the workspace."]})
		return data


class MessageSerializer(ModelSerializer):
	class Meta:
		model = Message
		fields = [Message.fields.id, Message.fields.role, Message.fields.content, Message.fields.created_at]
		read_only_fields = [Message.fields.id, Message.fields.role, Message.fields.created_at]
