from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import (m2m_changed, post_delete, post_save,
                                      pre_delete)
from django.urls import reverse
from simple_history.models import HistoricalRecords
# import reversion

from rard.research.models.mixins import HistoryViewMixin
from rard.utils.basemodel import (BaseModel, DatedModel, LockableModel,
                                  OrderableModel)




from django.dispatch import receiver
from simple_history.signals import (
    pre_create_historical_record,
    post_create_historical_record
)

from rard.users.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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
    print("Sent after saving historical record sender %s" % sender)
    print("kwargs %s" % str(kwargs))
    '''
    kwargs {
        'signal': <django.dispatch.dispatcher.Signal object at 0x7f41cfb12a60>, 
        'instance': <AnonymousFragment: Anonymous F2>, 
        'history_instance': <HistoricalAnonymousFragment: Anonymous F2 as of 2021-01-20 16:49:19.585515+00:00>, 
        'history_date': datetime.datetime(2021, 1, 20, 16, 49, 19, 585515, tzinfo=<UTC>), 
        'history_user': <SimpleLazyObject: <User: developer>>, 
        'history_change_reason': None, 
        'using': None
    }
    '''

    HistoricalRecordLog.objects.create(
        history_record=kwargs.get('history_instance'),
        history_user=kwargs.get('history_user'),
        history_date=kwargs.get('history_date')
    )