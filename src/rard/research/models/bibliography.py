import re

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel


class BibliographyItem(HistoryModelMixin, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.parent

    def __str__(self):
        r = self.author_surnames
        if self.year:
            r += ' [' + self.year + ']'
        title = re.sub(r'<[^>]*>', ' ', self.title)
        return r + ': ' + re.sub(r'\s+', ' ', title).strip()

    def get_absolute_url(self):
        return self.parent.get_absolute_url()

    class Meta:
        ordering = ['author_surnames', 'year']

    # allow these to point at different object types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    parent = GenericForeignKey()

    # string containing names of authors
    # e.g. Smith P, Jones M
    # ordering will be done on this field
    authors = models.CharField(max_length=512, blank=False)

    # comma-separated list of surnames of the authors, to be used for
    # ordering the entries in the list
    author_surnames = models.CharField(
        max_length=512, default='', blank=False,
        help_text='Comma-separated list of surnames to be used for ordering'
    )

    year = models.CharField(
        max_length=512, default='', blank=True,
        help_text='Optional date info to use for second-order '
        'sorting e.g. 1500a'
    )

    title = models.TextField(default='', blank=False)
