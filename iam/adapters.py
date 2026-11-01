from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.exceptions import ValidationError

from iam.models import User


class CustomAccountAdapter(DefaultAccountAdapter):
	def get_email_confirmation_url(self, request, emailconfirmation):
		return self.request.build_absolute_uri(f"/verify-email/{emailconfirmation.key}")


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
	def pre_social_login(self, request, social_login):
		if social_login.state.get('process') == 'connect':
			if social_login.is_existing and social_login.account.user_id != request.user.pk:
				raise ValidationError({'non_field_errors': ["This Google account is already connected to another IndexR account."]})
			return

		if social_login.account.provider != 'google' or social_login.is_existing:
			return
		email = social_login.user.email
		if not email:
			return

		existing_user = User.objects.filter(
			email=email,
		).first()
		if existing_user and existing_user.has_usable_password():
			EmailAddress.objects.filter(
				email=existing_user.email
			).update(verified=True, primary=True)
			social_login.connect(request, existing_user)

	def validate_disconnect(self, account, accounts) -> None:
		"""Refuses to remove a user's last way to sign in."""
		if len(accounts) == 1 and not account.user.has_usable_password():
			raise ValidationError({'non_field_errors': [
				"Set a password before disconnecting Google, so you can still sign in.",
			]})
