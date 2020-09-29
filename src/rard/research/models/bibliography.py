from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rard.utils.basemodel import BaseModel


class BibliographyItem(BaseModel):

    # allow these to point at different object types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    parent = GenericForeignKey()

    # the author, name and page of the named book or resource
    author = models.CharField(max_length=128, blank=False)

    title = models.CharField(max_length=128, blank=False)

    page = models.CharField(max_length=128, blank=False)
