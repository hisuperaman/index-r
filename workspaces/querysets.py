from django.db.models import Count, F, IntegerField, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce, Left

from enums.Workspace import MessageRole

LAST_QUESTION_LENGTH = 200
PREVIEW = "preview"
COUNT = "count"


class WorkspaceQuerySet(QuerySet):

	def with_activity(self):
		"""Workspaces annotated with their paper and question counts, last question and last activity."""
		from workspaces.models import Message, WorkspacePaper

		workspace = OuterRef(self.model.fields.id)
		messages = Message.objects.filter(workspace=workspace).order_by()
		questions = messages.filter(role=MessageRole.USER)
		papers = WorkspacePaper.objects.filter(workspace=workspace).order_by()
		newest_first = Message.fields.created_at.desc()
		return self.annotate(
			_paper_count=Coalesce(Subquery(self.count_of(papers), output_field=IntegerField()), 0),
			_question_count=Coalesce(Subquery(self.count_of(questions), output_field=IntegerField()), 0),
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
