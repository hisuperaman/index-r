from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, DateTimeField, IntegerField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from papers.models import Paper
from papers.serializers import ChunkSerializer, PaperSerializer
from workspaces.models import Message, MessageCitation, Workspace, WorkspacePaper


class WorkspaceSerializer(ModelSerializer):
	paper_count = IntegerField(read_only=True)
	question_count = IntegerField(read_only=True)
	last_question = CharField(read_only=True, allow_null=True)
	last_activity_at = DateTimeField(read_only=True)

	class Meta:
		model = Workspace
		read_only_fields = [
			Workspace.fields.id, Workspace.fields.created_at, Workspace.fields.updated_at, 'paper_count',
			'question_count', 'last_question', 'last_activity_at',
		]
		fields = [*read_only_fields, Workspace.fields.name, Workspace.fields.papers_only]


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


class MessageCitationSerializer(ModelSerializer):
	chunk = ChunkSerializer(read_only=True)

	class Meta:
		model = MessageCitation
		fields = [MessageCitation.fields.number, MessageCitation.fields.chunk]
		read_only_fields = fields


class MessageSerializer(ModelSerializer):
	citations = MessageCitationSerializer(many=True, read_only=True)

	class Meta:
		model = Message
		read_only_fields = [Message.fields.id, Message.fields.role, Message.fields.created_at, 'citations']
		fields = [*read_only_fields, Message.fields.content]


class MentionedPaperSerializer(PaperSerializer):
	mention_count = IntegerField(source='_mention_count', read_only=True)
	last_mentioned_at = DateTimeField(source='_last_mentioned_at', read_only=True)
	in_workspace = BooleanField(source='_in_workspace', read_only=True)

	class Meta(PaperSerializer.Meta):
		fields = [*PaperSerializer.Meta.fields, 'mention_count', 'last_mentioned_at', 'in_workspace']
		read_only_fields = fields
