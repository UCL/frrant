from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rard.utils.basemodel import BaseModel


class BibliographyItem(BaseModel):

    class Meta:
        ordering = ['authors']

    # allow these to point at different object types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    parent = GenericForeignKey()

    # string containing names of authors
    # e.g. Smith P, Jones M
    # ordering will be done on this field
    authors = models.CharField(max_length=512, blank=True)

    content = models.TextField(default='', blank=False)
