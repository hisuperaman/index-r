from django.db.models import Count, Exists, F, IntegerField, OuterRef, Prefetch, QuerySet, Subquery
from django.db.models.functions import Coalesce, Left

from enums.Workspace import MessageRole, TrackingUpdateLookup

LAST_QUESTION_LENGTH = 200
PREVIEW = "preview"
COUNT = "count"


class WorkspaceQuerySet(QuerySet):

	def with_activity(self):
		"""Workspaces annotated with their paper and question counts, last question and last activity."""
		from workspaces.models import Message, TrackingUpdate, WorkspacePaper

		workspace = OuterRef(self.model.fields.id)
		messages = Message.objects.filter(workspace=workspace).order_by()
		questions = messages.filter(role=MessageRole.USER)
		papers = WorkspacePaper.objects.filter(workspace=workspace).order_by()
		unseen_updates = TrackingUpdate.objects.filter(
			workspace=workspace,
			created_at__gt=Coalesce(OuterRef(self.model.fields.updates_seen_at), OuterRef(self.model.fields.created_at)),
		).order_by()
		newest_first = Message.fields.created_at.desc()
		return self.annotate(
			_paper_count=Coalesce(Subquery(self.count_of(papers), output_field=IntegerField()), 0),
			_question_count=Coalesce(Subquery(self.count_of(questions), output_field=IntegerField()), 0),
			_unseen_update_count=Coalesce(Subquery(self.count_of(unseen_updates), output_field=IntegerField()), 0),
			_last_question=Subquery(
				questions.order_by(newest_first)
				.annotate(preview=Left(Message.fields.content, LAST_QUESTION_LENGTH)).values(PREVIEW)[:1]
			),
			_last_activity_at=Coalesce(
				Subquery(messages.order_by(newest_first).values(Message.fields.created_at)[:1]),
				F(self.model.fields.created_at),
			),
		)

	@staticmethod
	def count_of(rows: QuerySet) -> QuerySet:
		"""A one-value subquery counting `rows` for the outer workspace."""
		fields = rows.model.fields
		return rows.values(fields.workspace).annotate(count=Count(fields.id)).values(COUNT)


class TrackingUpdateQuerySet(QuerySet):

	def unseen(self):
		"""Updates found since their workspace's updates were last seen."""
		seen_at = Coalesce(
			F(TrackingUpdateLookup.workspace__updates_seen_at.value), F(TrackingUpdateLookup.workspace__created_at.value),
		)
		return self.filter(created_at__gt=seen_at)

	def with_details(self):
		"""Updates with their papers, topic and authors loaded, and whether the paper is already in the workspace."""
		from papers.models import PaperAuthor

		return self.with_in_workspace().select_related(
			self.model.fields.paper, self.model.fields.topic, self.model.fields.cited_paper,
		).prefetch_related(Prefetch(
			TrackingUpdateLookup.paper__paper_authors.value,
			queryset=PaperAuthor.objects.select_related(PaperAuthor.fields.author),
		))

	def with_in_workspace(self):
		"""Updates annotated with whether their paper is already in their workspace."""
		from workspaces.models import WorkspacePaper

		return self.annotate(_in_workspace=Exists(WorkspacePaper.objects.filter(
			workspace=OuterRef(self.model.fields.workspace), paper=OuterRef(self.model.fields.paper),
		)))
