from django.db.models import Count, F, IntegerField, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce, Left

from enums.Workspace import MessageRole

LAST_QUESTION_LENGTH = 200


class WorkspaceQuerySet(QuerySet):

	def with_activity(self):
		"""Workspaces annotated with their paper and question counts, last question and last activity."""
		from workspaces.models import Message, WorkspacePaper

		messages = Message.objects.filter(workspace=OuterRef("pk")).order_by()
		questions = messages.filter(role=MessageRole.USER)
		papers = WorkspacePaper.objects.filter(workspace=OuterRef("pk")).order_by()
		return self.annotate(
			_paper_count=Coalesce(Subquery(self.count_of(papers), output_field=IntegerField()), 0),
			_question_count=Coalesce(Subquery(self.count_of(questions), output_field=IntegerField()), 0),
			_last_question=Subquery(
				questions.order_by("-created_at").annotate(preview=Left("content", LAST_QUESTION_LENGTH)).values("preview")[:1]
			),
			_last_activity_at=Coalesce(
				Subquery(messages.order_by("-created_at").values("created_at")[:1]), F("created_at"),
			),
		)

	@staticmethod
	def count_of(rows: QuerySet) -> QuerySet:
		"""A one-value subquery counting `rows` for the outer workspace."""
		return rows.values("workspace").annotate(count=Count("pk")).values("count")
