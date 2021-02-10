from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from rard.users.models import User


class HistoricalRecordLog(models.Model):

    class Meta:
        ordering = ['history_date']

    def get_sentinel_user():
        from allauth.utils import get_user_model
        return get_user_model().objects.get_or_create(
            username='deleted',
            first_name='Deleted',
            last_name='User'
        )[0]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    # auto-deletes e.g. when the history records are pruned
    history_record = GenericForeignKey()

    history_user = models.ForeignKey(
        User, related_name='history_log', default=None, null=True,
        on_delete=models.SET(get_sentinel_user)
    )
    history_date = models.DateTimeField(editable=False)


@receiver(post_create_historical_record)
def post_create_historical_record_callback(sender, **kwargs):

    HistoricalRecordLog.objects.create(
        history_record=kwargs.get('history_instance'),
        history_user=kwargs.get('history_user'),
        history_date=kwargs.get('history_date')
    )
