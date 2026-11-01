from django.db.models import QuerySet

from iam.models import User


def scope_to_user(queryset: QuerySet, user: User | None, field: str = 'user') -> QuerySet:
	"""Narrows `queryset` to the rows `user` owns, reached through `field`, or to none without a logged-in user."""
	if user is None or not user.is_authenticated:
		return queryset.none()
	return queryset.filter(**{field: user})
