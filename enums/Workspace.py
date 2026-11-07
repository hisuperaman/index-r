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


class TrackingUpdateKind(TextChoices):
	NEW_PAPER = 'new_paper', 'New paper'
	NEW_CITATION = 'new_citation', 'New citation'
	NEW_VERSION = 'new_version', 'New version'


class WorkspaceLookup(FieldEnum):
	user__email = 'user__email'
	last_activity_at = '_last_activity_at'


class WorkspacePaperLookup(FieldEnum):
	paper__paper_authors = 'paper__paper_authors'
	is_tracked = 'is_tracked'


class TrackingUpdateLookup(FieldEnum):
	kind = 'kind'
	in_workspace = '_in_workspace'
	workspace__updates_seen_at = 'workspace__updates_seen_at'
	workspace__created_at = 'workspace__created_at'
	paper__paper_authors = 'paper__paper_authors'


class MessageCitationLookup(FieldEnum):
	chunk__paper = 'chunk__paper'
	message__workspace = 'message__workspace'
	message__created_at = 'message__created_at'
