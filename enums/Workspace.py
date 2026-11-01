from django.db.models.enums import TextChoices


class MessageRole(TextChoices):
	USER = 'user', 'User'
	ASSISTANT = 'assistant', 'Assistant'


class AskStage(TextChoices):
	EXPANDING = 'expanding', 'Understanding your question'
	SEARCHING = 'searching', 'Looking through papers'
	DISCOVERING = 'discovering', 'Finding new papers'
	INGESTING = 'ingesting', 'Reading new papers'
	ANSWERING = 'answering', 'Writing the answer'
