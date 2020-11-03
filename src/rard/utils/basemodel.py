from django.conf import settings
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from model_utils.models import TimeStampedModel


class ObjectLock(models.Model):

    class Meta:
        app_label = 'research'

    locked_at = models.DateTimeField(null=True, editable=False)
    locked_by = models.ForeignKey(
        'users.User',
        null=True,
        editable=False,
        on_delete=models.SET_NULL
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    content_object = GenericForeignKey()


class ObjectLockRequest(TimeStampedModel, models.Model):
    class Meta:
        app_label = 'research'

    # a request to break the lock. All deleted when the lock is deleted
    object_lock = models.ForeignKey(ObjectLock, on_delete=models.CASCADE)

    from_user = models.ForeignKey('users.User', on_delete=models.CASCADE)


class BaseModel(TimeStampedModel, models.Model):

    # defines a base model with any required
    # additional common functionality
    class Meta:
        abstract = True


class LockableModel(models.Model):

    class Meta:
        abstract = True

    object_locks = GenericRelation(ObjectLock)

    def get_object_lock(self):
        return self.object_locks.first()

    def lock(self, user):
        ObjectLock.objects.create(
            locked_at=timezone.now(),
            locked_by=user,
            content_object=self
        )

    def unlock(self):

        # collect data emails using info before we delete it
        # and if deletion works okay then send the mails after
        # (we don't have access to the info once we delete it)
        email_data_list = []

        object_lock = self.get_object_lock()

        # notify anyone with a lock request of the event
        for lock_request in object_lock.objectlockrequest_set.all():

            html_email_template = 'research/emails/item_unlocked.html'
            current_site = get_current_site(None)
            context = {
                'user': object_lock.locked_by,
                'from_user': lock_request.from_user,
                'lock': object_lock,
                'site_name': current_site.name,
                'domain': current_site.domain,
            }
            content = render_to_string(html_email_template, context)
            email_data = [
                (
                    'The item you requested has become available',
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [lock_request.from_user.email],
                ),
                {
                    'html_message': content,
                    'fail_silently': False
                }
            ]
            email_data_list.append(email_data)

        # delete any lock records
        self.object_locks.all().delete()

        # send the mails we prepared
        for args, kwargs in email_data_list:
            send_mail(*args, **kwargs)

    def is_locked(self):
        return self.object_locks.exists()

    @property
    def locked_by(self):
        if self.is_locked():
            return self.get_object_lock().locked_by
        return None

    @property
    def locked_at(self):
        if self.is_locked():
            return self.get_object_lock().locked_at
        return None

    def request_lock(self, from_user):
        self.get_object_lock().objectlockrequest_set.create(
            from_user=from_user
        )
        object_lock = self.get_object_lock()

        # notify lock owner of the request
        html_email_template = 'research/emails/request_lock.html'
        current_site = get_current_site(None)
        context = {
            'user': object_lock.locked_by,
            'from_user': from_user,
            'lock': object_lock,
            'site_name': current_site.name,
            'domain': current_site.domain,
        }
        content = render_to_string(html_email_template, context)
        send_mail(
            'Request to edit record',
            '',
            settings.DEFAULT_FROM_EMAIL,
            [self.get_object_lock().locked_by.email],
            html_message=content,
            fail_silently=False,
        )


class DatedModel(models.Model):
    # for models that have a date range or value, such as
    # antiquarians, works and books

    class Meta:
        abstract = True

    YEAR_RANGE = 'range'
    YEAR_BEFORE = 'before'
    YEAR_AFTER = 'after'
    YEAR_SINGLE = 'single'

    YEAR_INFO_CHOICES = [
        (YEAR_RANGE, 'From/To'),
        (YEAR_BEFORE, 'Before'),
        (YEAR_AFTER, 'After'),
        (YEAR_SINGLE, 'Single Year'),
    ]

    # negative means BC, positive is AD
    # the meaning of year1 and year depends on type of date info we have
    year1 = models.IntegerField(default=None, null=True, blank=True)
    year2 = models.IntegerField(default=None, null=True, blank=True)
    circa1 = models.BooleanField(default=False)
    circa2 = models.BooleanField(default=False)

    # the type of year info we have
    year_type = models.CharField(
        max_length=16,
        choices=YEAR_INFO_CHOICES,
        blank=True
    )

    @classmethod
    def _bcad(cls, year):
        try:
            if year < 0:
                return '{} BC'.format(abs(year))
            else:
                return '{} AD'.format(abs(year))
        except TypeError:
            return ''

    def display_date_range(self, prepend=None):
        if not self.year_type:
            return ''

        if self.year_type == self.YEAR_RANGE:
            if self.year1 * self.year2 < 0:
                # they are of different sides of zero AD
                # so show BC or AD on both
                display_year1 = self._bcad(self.year1)
            else:
                display_year1 = str(abs(self.year1))

            if self.circa1:
                display_year1 = 'c. ' + display_year1

            display_year2 = self._bcad(self.year2)

            if self.circa2:
                display_year2 = 'c. ' + display_year2

            info = ' to '.join([display_year1, display_year2])
            return (
                '{} from {}'.format(prepend, info) if prepend
                else 'From {}'.format(info)
            )
        else:
            if self.year_type == self.YEAR_SINGLE:
                stub = ''
            else:
                stub = self.get_year_type_display()
                if prepend:
                    stub = stub.lower()

            circa1 = 'c. ' if self.circa1 else ''
            info = '{} {}{}'.format(
                stub,
                circa1,
                self._bcad(self.year1)
            ).strip()

            return '{} {}'.format(prepend, info) if prepend else info
