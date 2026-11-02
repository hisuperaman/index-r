from django.conf import settings
from django.db.models import CASCADE, CharField, CheckConstraint, DateTimeField, ForeignKey, Q

from integrations.querysets import ApiTokenQuerySet
from server.models import PrimaryModel


class ApiToken(PrimaryModel):
	"""A personal access token that lets an MCP client act as its user."""
	user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="api_tokens")
	name = CharField(max_length=100)
	prefix = CharField(max_length=16)
	key_hash = CharField(max_length=64, unique=True)
	last_used_at = DateTimeField(blank=True, null=True)

	objects = ApiTokenQuerySet.as_manager()

	class Meta:
		constraints = [
			CheckConstraint(condition=~Q(name=""), name="api_token_name_not_blank"),
		]

	def __str__(self):
		return f"{self.name} ({self.prefix}…)"
