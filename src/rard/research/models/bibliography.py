from django.db import models

from rard.utils.basemodel import BaseModel


class BibliographyItem(BaseModel):
    parent = models.ForeignKey('CommentableText', on_delete=models.CASCADE)

    # the author, name and page of the named book or resource
    author = models.CharField(max_length=128, blank=False)

    title = models.CharField(max_length=128, blank=False)

    page = models.CharField(max_length=128, blank=False)
