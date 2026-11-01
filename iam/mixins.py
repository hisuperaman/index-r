from iam.scoping import scope_to_user


class UserScopedMixin:
	"""Limits a view's queryset to the caller's own rows and makes the caller the owner of what it creates."""
	scope_field = 'user'

	def get_queryset(self):
		return scope_to_user(super().get_queryset(), self.request.user, self.scope_field)

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)
