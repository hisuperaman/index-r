from django.core.management.base import BaseCommand

from workspaces.models import TrackingUpdate
from workspaces.services import TrackingService


class Command(BaseCommand):
	help = "Checks every tracked topic and paper now, without waiting for the daily scheduled check."

	def handle(self, *args, **options):
		before = TrackingUpdate.objects.count()
		TrackingService.check_all()
		self.stdout.write(f"Found {TrackingUpdate.objects.count() - before} new updates.")
