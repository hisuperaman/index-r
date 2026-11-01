from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.serializers import PasswordChangeSerializer as _PasswordChangeSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework.fields import BooleanField, CharField
from rest_framework.serializers import ModelSerializer

from enums.User import UserField
from iam.models import User


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



class UserSerializer(ModelSerializer):
	has_password = BooleanField(source='has_usable_password', read_only=True)

	class Meta:
		model = User
		read_only_fields = [UserField.id.value, UserField.email.value, 'has_password']
		fields = [*read_only_fields, UserField.first_name.value, UserField.last_name.value]



class PasswordChangeSerializer(_PasswordChangeSerializer):
	"""Lets a user who signs in only with Google set a first password without an old one."""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.user and not self.user.has_usable_password():
			self.old_password_field_enabled = False
			self.fields.pop('old_password', None)


class SocialAccountSerializer(ModelSerializer):
	email = CharField(source='extra_data.email', read_only=True, default=None)

	class Meta:
		model = SocialAccount
		read_only_fields = ['id', 'provider', 'email', 'date_joined']
		fields = read_only_fields
