import hashlib
import secrets
from datetime import timedelta

from django.db.models import Q, QuerySet
from django.utils import timezone

TOKEN_PREFIX = "ixr_"
PREFIX_LENGTH = len(TOKEN_PREFIX) + 8
LAST_USED_RESOLUTION = timedelta(minutes=5)


def hash_token(raw: str) -> str:
	"""The SHA-256 of a token, which is all that is stored."""
	return hashlib.sha256(raw.encode()).hexdigest()


class ApiTokenQuerySet(QuerySet):

	def issue(self, user, name: str):
		"""Creates a token for `user` and returns it with its raw value, which is never stored."""
		raw = TOKEN_PREFIX + secrets.token_urlsafe(32)
		token = self.create(user=user, name=name, prefix=raw[:PREFIX_LENGTH], key_hash=hash_token(raw))
		token.raw_token = raw
		return token

	def authenticate(self, raw: str):
		"""Returns the token matching `raw`, noting when it was used, or None."""
		if not raw or not raw.startswith(TOKEN_PREFIX):
			return None
		token = self.select_related(self.model.fields.user).filter(key_hash=hash_token(raw), user__is_active=True).first()
		if token is None:
			return None
		now = timezone.now()
		stale = Q(last_used_at__isnull=True) | Q(last_used_at__lt=now - LAST_USED_RESOLUTION)
		self.filter(stale, pk=token.pk).update(last_used_at=now)
		return token
