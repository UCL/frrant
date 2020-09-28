from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from rard.utils.basemodel import BaseModel


class TextObjectField(BaseModel):
    # store text in a separate object to allow comments and/or
    # bib items to be associated with them
    content = models.TextField(default='', blank=True)

    comments = GenericRelation('Comment', related_query_name='text_fields')

    references = GenericRelation(
        'BibliographyItem', related_query_name='text_fields'
    )

    def __str__(self):
        return self.content
