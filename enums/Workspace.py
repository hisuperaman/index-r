from django.db.models.enums import TextChoices

from enums.Enum import FieldEnum


class MessageRole(TextChoices):
	USER = 'user', 'User'
	ASSISTANT = 'assistant', 'Assistant'


class AskStage(TextChoices):
	EXPANDING = 'expanding', 'Understanding your question'
	SEARCHING = 'searching', 'Looking through papers'
	DISCOVERING = 'discovering', 'Finding new papers'
	INGESTING = 'ingesting', 'Reading new papers'
	ANSWERING = 'answering', 'Writing the answer'


class WorkspaceLookup(FieldEnum):
	user__email = 'user__email'
	last_activity_at = '_last_activity_at'


class WorkspacePaperLookup(FieldEnum):
	paper__paper_authors = 'paper__paper_authors'


class MessageCitationLookup(FieldEnum):
	chunk__paper = 'chunk__paper'
	message__workspace = 'message__workspace'
	message__created_at = 'message__created_at'
