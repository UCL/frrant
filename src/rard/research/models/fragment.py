from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse

from rard.research.models.base import HistoricalBaseModel


class Fragment(HistoricalBaseModel):

    # fragments can also have topics
    topics = models.ManyToManyField('Topic', blank=True)

    original_texts = GenericRelation(
        'OriginalText', related_query_name='original_texts'
    )

    def get_absolute_url(self):
        return reverse('fragment:detail', kwargs={'pk': self.pk})


Fragment.init_text_object_fields()
