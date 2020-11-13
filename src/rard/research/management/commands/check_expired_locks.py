from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from rard.utils.basemodel import ObjectLock


class Command(BaseCommand):

    help = 'Checks for locks that have expired'

    def handle(self, *args, **options):
        try:
            stale = ObjectLock.objects.filter(
                locked_until__isnull=False,
                locked_until__lt=timezone.now()
            )
            for lock in stale:
                # the following will send appropriate emails
                lock.content_object.unlock()
        except Exception as err:
            raise CommandError(str(err))
