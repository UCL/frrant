from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from rard.utils.basemodel import ObjectLock


class Command(BaseCommand):

    help = 'Checks for indefinite locks that have been held for a long time'

    def handle(self, *args, **options):
        warn_after_days = 5
        limit = timezone.now() - timedelta(days=warn_after_days)
        try:
            indefinite = ObjectLock.objects.filter(
                locked_until__isnull=True,
                locked_at__lt=limit
            )
            for lock in indefinite:
                # send appropriate email
                lock.content_object.send_long_lock_email()

        except Exception as err:
            raise CommandError(str(err))
