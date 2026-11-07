from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, DateTimeField, IntegerField
from rest_framework.relations import PrimaryKeyRelatedField
from django.utils import timezone
from rest_framework.serializers import ModelSerializer

from enums.Paper import PaperLookup
from enums.Workspace import TrackingUpdateLookup, WorkspacePaperLookup
from papers.models import Paper
from papers.serializers import ChunkSerializer, PaperBasicSerializer, PaperSerializer
from workspaces.models import Message, MessageCitation, TrackedTopic, TrackingUpdate, Workspace, WorkspacePaper

MAX_TOPICS_PER_WORKSPACE = 10


class WorkspaceSerializer(ModelSerializer):
	paper_count = IntegerField(read_only=True)
	question_count = IntegerField(read_only=True)
	last_question = CharField(read_only=True, allow_null=True)
	last_activity_at = DateTimeField(read_only=True)
	unseen_update_count = IntegerField(read_only=True)

	class Meta:
		model = Workspace
		read_only_fields = [
			Workspace.fields.id, Workspace.fields.created_at, Workspace.fields.updated_at, 'paper_count',
			'question_count', 'last_question', 'last_activity_at', 'unseen_update_count',
			Workspace.fields.updates_seen_at,
		]
		fields = [*read_only_fields, Workspace.fields.name, Workspace.fields.papers_only]


class WorkspacePaperSerializer(ModelSerializer):
	paper = PaperSerializer(read_only=True)
	paper_id = PrimaryKeyRelatedField(source=WorkspacePaper.fields.paper, queryset=Paper.objects.none(), write_only=True)
	tracked = BooleanField(source=WorkspacePaperLookup.is_tracked.value, required=False)

	class Meta:
		model = WorkspacePaper
		read_only_fields = [WorkspacePaper.fields.paper, WorkspacePaper.fields.created_at, WorkspacePaper.fields.tracked_at]
		fields = [*read_only_fields, 'paper_id', 'tracked']

	def __init__(self, *args, workspace: Workspace | None = None, **kwargs):
		super().__init__(*args, **kwargs)
		self.workspace = workspace
		if workspace is not None:
			self.fields['paper_id'].queryset = Paper.objects.visible_to(workspace.user)
		if isinstance(self.instance, WorkspacePaper):
			self.fields['paper_id'].read_only = True

	def validate(self, data):
		data = super().validate(data)
		if self.instance is None and WorkspacePaper.objects.filter(
				workspace=self.workspace, paper=data[WorkspacePaper.fields.paper],
		).exists():
			raise ValidationError({'paper_id': ["This paper is already in the workspace."]})
		paper = data.get(WorkspacePaper.fields.paper) or self.instance.paper
		if data.get(WorkspacePaperLookup.is_tracked.value) and paper.is_private:
			raise ValidationError({'tracked': ["Your own uploads can't be tracked for new citations or versions."]})
		return data

	def create(self, validated_data):
		return super().create(self.with_tracked_at(validated_data))

	def update(self, instance, validated_data):
		return super().update(instance, self.with_tracked_at(validated_data))

	def with_tracked_at(self, validated_data: dict) -> dict:
		"""Turns the written `tracked` flag into the time tracking started, keeping that time if already tracked."""
		if WorkspacePaperLookup.is_tracked.value not in validated_data:
			return validated_data
		tracked = validated_data.pop(WorkspacePaperLookup.is_tracked.value)
		current = self.instance.tracked_at if self.instance else None
		return {**validated_data, WorkspacePaper.fields.tracked_at: (current or timezone.now()) if tracked else None}


class TrackedTopicSerializer(ModelSerializer):

	class Meta:
		model = TrackedTopic
		read_only_fields = [TrackedTopic.fields.id, TrackedTopic.fields.created_at, TrackedTopic.fields.checked_at]
		fields = [*read_only_fields, TrackedTopic.fields.query]

	def __init__(self, *args, workspace: Workspace | None = None, **kwargs):
		super().__init__(*args, **kwargs)
		self.workspace = workspace

	def validate_query(self, query):
		topics = TrackedTopic.objects.filter(workspace=self.workspace)
		if topics.filter(query__iexact=query).exists():
			raise ValidationError("This workspace already tracks this topic.")
		if topics.count() >= MAX_TOPICS_PER_WORKSPACE:
			raise ValidationError(f"A workspace can track up to {MAX_TOPICS_PER_WORKSPACE} topics.")
		return query


class TrackingUpdateSerializer(ModelSerializer):
	kind = CharField(read_only=True)
	paper = PaperSerializer(read_only=True)
	topic = TrackedTopicSerializer(read_only=True)
	cited_paper = PaperBasicSerializer(read_only=True)
	in_workspace = BooleanField(source=TrackingUpdateLookup.in_workspace.value, read_only=True)

	class Meta:
		model = TrackingUpdate
		fields = [
			TrackingUpdate.fields.id, TrackingUpdateLookup.kind.value, TrackingUpdate.fields.created_at,
			TrackingUpdate.fields.paper, TrackingUpdate.fields.topic, TrackingUpdate.fields.cited_paper, 'in_workspace',
		]
		read_only_fields = fields


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
		read_only_fields = [Message.fields.id, Message.fields.role, Message.fields.created_at, Message.fields.citations]
		fields = [*read_only_fields, Message.fields.content]


class MentionedPaperSerializer(PaperSerializer):
	mention_count = IntegerField(source=PaperLookup.mention_count.value, read_only=True)
	last_mentioned_at = DateTimeField(source=PaperLookup.last_mentioned_at.value, read_only=True)
	in_workspace = BooleanField(source=PaperLookup.in_workspace.value, read_only=True)

	class Meta(PaperSerializer.Meta):
		fields = [*PaperSerializer.Meta.fields, 'mention_count', 'last_mentioned_at', 'in_workspace']
		read_only_fields = fields
