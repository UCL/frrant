from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rard.utils.basemodel import BaseModel


class BibliographyItem(BaseModel):

    class Meta:
        ordering = ['author_name']

    # allow these to point at different object types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    parent = GenericForeignKey()

    author_name = models.CharField(max_length=128, blank=False)

    content = models.TextField(default='', blank=False)
