from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
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

    def get_related_object(self):
        # what model instance owns this text object field?
        related_fields = [
            f for f in self._meta.get_fields() if f.auto_created
            and not f.concrete
        ]
        for field in related_fields:
            try:
                return getattr(self, field.name)
            except ObjectDoesNotExist:
                pass
        return None

    @property
    def fragment(self):
        from rard.research.models import Fragment
        related = self.get_related_object()
        return related if isinstance(related, Fragment) else None

    @property
    def testimonium(self):
        from rard.research.models import Testimonium
        related = self.get_related_object()
        return related if isinstance(related, Testimonium) else None

    @property
    def antiquarian(self):
        from rard.research.models import Antiquarian
        related = self.get_related_object()
        return related if isinstance(related, Antiquarian) else None
