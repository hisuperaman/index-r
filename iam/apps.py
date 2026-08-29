from django.apps import AppConfig


class AuthConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'iam'

	def ready(self):
		import iam.signals
