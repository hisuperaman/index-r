from allauth.account.models import EmailAddress
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework.fields import CharField

from enums.User import UserField


class CustomRegisterSerializer(RegisterSerializer):
	username = None
	first_name = CharField(required=True, max_length=150)
	last_name = CharField(required=False, max_length=150, allow_blank=True)

	def validate_first_name(self, value: str) -> str:
		return value.strip()

	def validate_last_name(self, value: str) -> str:
		return value.strip()

	def validate_email(self, email):
		email = super().validate_email(email)
		# delete old unverified User to avoid IntegrityError due to duplicate email
		email_obj: EmailAddress = EmailAddress.objects.filter(email=email).select_related("user").first()
		if email_obj and not email_obj.verified:
			email_obj.user.delete()

		return email

	def get_cleaned_data(self):
		return {
			'password1': self.validated_data.get('password1', ''),
			UserField.email.value: self.validated_data.get(UserField.email.value, ''),
		}

	def custom_signup(self, request, user):
		user.first_name = self.validated_data[UserField.first_name.value]
		user.last_name = self.validated_data[UserField.last_name.value]
		user.save(update_fields=[UserField.first_name.value, UserField.last_name.value])
