from allauth.account.models import EmailAddress
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.core.mail import send_mail
from django.db.models import EmailField, CharField, BooleanField, DateTimeField
from django.utils import timezone


class MyUserManager(BaseUserManager):
	def create_user(self, email, password=None):
		"""
		Creates and saves a User with the given email and password.
		"""
		if not email:
			raise ValueError('Users must have an email address')

		user = self.model(
			email=self.normalize_email(email),
		)

		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None):
		"""
		Creates and saves a superuser with the given email, date of
		birth and password.
		"""
		user = self.create_user(
			email,
			password=password,
		)
		user.is_staff = True
		user.is_superuser = True
		user.is_active = True
		user.save(using=self._db)
		return user


class User(AbstractBaseUser, PermissionsMixin):
	first_name = CharField(max_length=150, blank=True, verbose_name='first name')
	last_name = CharField(max_length=150, blank=True, verbose_name='last name')
	email = EmailField(unique=True, verbose_name='email address')

	is_staff = BooleanField(
		default=False,
		help_text="Designates whether the user can log into this admin site.",
		verbose_name="staff status"
	)
	is_active = BooleanField(
		default=True,
		help_text=(
			"Designates whether this user should be treated as active. "
			"Unselect this instead of deleting accounts."
		),
		verbose_name="active"
	)
	date_joined = DateTimeField(default=timezone.now, verbose_name="date joined")

	objects = MyUserManager()

	EMAIL_FIELD = "email"
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)

	class Meta:
		verbose_name = "user"
		verbose_name_plural = "users"

	def clean(self):
		super().clean()
		self.email = self.__class__.objects.normalize_email(self.email)

	def get_full_name(self):
		"""
		Return the first_name plus the last_name, with a space in between.
		"""
		full_name = "%s %s" % (self.first_name, self.last_name)
		return full_name.strip()

	def get_short_name(self):
		"""Return the short name for the user."""
		return self.first_name

	def email_user(self, subject, message, from_email=None, **kwargs):
		"""Send an email to this user."""
		send_mail(subject, message, from_email, [self.email], **kwargs)
