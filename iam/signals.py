from allauth.account.models import EmailAddress
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from iam.models import User


@receiver(post_save, sender=User)
def sync_email_address(sender, instance, created, **kwargs):
	if not instance.email:
		return

	def create_email_obj():
		email_obj, _ = EmailAddress.objects.get_or_create(
			user=instance,
			defaults={
				"email": instance.email,
				"primary": True,
				"verified": False,
			},
		)

		if email_obj.email != instance.email:
			email_obj.email = instance.email
			email_obj.primary = True
			email_obj.verified = False
			email_obj.save()

	# on_commit ensures allauth EmailAddress logic runs completely first to avoid race condition
	transaction.on_commit(create_email_obj)
