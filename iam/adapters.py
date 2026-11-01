from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from iam.models import User


class CustomAccountAdapter(DefaultAccountAdapter):
	def get_email_confirmation_url(self, request, emailconfirmation):
		return self.request.build_absolute_uri(f"/verify-email/{emailconfirmation.key}")


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
	def pre_social_login(self, request, social_login):
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
