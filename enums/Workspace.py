from django.db.models.enums import TextChoices


class MessageRole(TextChoices):
	USER = 'user', 'User'
	ASSISTANT = 'assistant', 'Assistant'


class AskStage(TextChoices):
	EXPANDING = 'expanding', 'Expanding the question'
	SEARCHING = 'searching', 'Searching the corpus'
	DISCOVERING = 'discovering', 'Discovering new papers'
	INGESTING = 'ingesting', 'Indexing new papers'
	ANSWERING = 'answering', 'Writing the answer'
