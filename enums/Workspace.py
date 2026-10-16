from django.db.models.enums import TextChoices


class MessageRole(TextChoices):
	USER = 'user', 'User'
	ASSISTANT = 'assistant', 'Assistant'
