from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse

from .base import HistoricalBaseModel


class Testimonium(HistoricalBaseModel):

    original_texts = GenericRelation(
        'OriginalText', related_query_name='original_texts'
    )

    def get_absolute_url(self):
        return reverse('testimonium:detail', kwargs={'pk': self.pk})


Testimonium.init_text_object_fields()
