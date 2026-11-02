from django.db.models.enums import TextChoices

from enums.Enum import FieldEnum


class Role(TextChoices):
	SCHOOL_ADMIN = 'school_admin', 'School Admin'
	TEACHER = 'teacher', 'Teacher'
	STUDENT = 'student', 'Student'


class UserField(FieldEnum):
	id = 'id'
	school = 'school'
	username = 'username'
	first_name = 'first_name'
	last_name = 'last_name'
	email = 'email'
	password = 'password'
	phone = 'phone'
	dob = 'dob'
	is_active = 'is_active'
	is_superuser = 'is_superuser'
	is_staff = 'is_staff'
	last_login = 'last_login'
	date_joined = 'date_joined'
	groups = 'groups'
	user_permissions = 'user_permissions'
	has_usable_password = 'has_usable_password'


class EmailAddressField(FieldEnum):
	user = 'user'
	email = 'email'


class SocialAccountField(FieldEnum):
	id = 'id'
	provider = 'provider'
	date_joined = 'date_joined'
	extra_data = 'extra_data'
