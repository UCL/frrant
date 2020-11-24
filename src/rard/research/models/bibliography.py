from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rard.utils.basemodel import BaseModel


class BibliographyItem(BaseModel):

    class Meta:
        ordering = ['author_surnames', 'year']

    # allow these to point at different object types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    parent = GenericForeignKey()

    # string containing names of authors
    # e.g. Smith P, Jones M
    # ordering will be done on this field
    authors = models.CharField(max_length=512, blank=True)

    # comma-separated list of surnames of the authors, to be used for
    # ordering the entries in the list
    author_surnames = models.CharField(
        max_length=512, default='', blank=False,
        help_text='Comma-separated list of surnames to be used for ordering'
    )

    year = models.IntegerField(
        default=None, null=True, blank=True,
        help_text='Optional year to use for second-order sorting of entries'
    )

    content = models.TextField(default='', blank=False)
