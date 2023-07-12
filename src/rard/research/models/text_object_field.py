from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel, DynamicTextField


class TextObjectField(HistoryModelMixin, BaseModel):
    history = HistoricalRecords()

    def related_lock_object(self):
        return self.get_related_object()

    # store text in a separate object to allow its own
    # audit trail to be held
    content = DynamicTextField(default="", blank=True)

    comments = GenericRelation("Comment", related_query_name="text_fields")

    references = GenericRelation("BibliographyItem", related_query_name="text_fields")

    def get_history_title(self):
        obj = self.get_related_object()
        if obj.__class__.__name__ in ["Antiquarian", "Work", "Book"]:
            return "Introduction"
        return "Commentary"

    def __str__(self):
        return self.content

    def get_related_object(self):
        # what model instance owns this text object field?
        related_fields = [
            f for f in self._meta.get_fields() if f.auto_created and not f.concrete
        ]
        for field in related_fields:
            try:
                return getattr(self, field.name)
            except ObjectDoesNotExist:
                pass
        return None

    def save(self, *args, **kwargs):
        # save the parent object so the plain intro/commentary is processed
        obj = self.get_related_object()
        obj.save()
        super().save(*args, **kwargs)

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

    @property
    def work(self):
        from rard.research.models import Work

        related = self.get_related_object()
        return related if isinstance(related, Work) else None

    @property
    def book(self):
        from rard.research.models import Book

        related = self.get_related_object()
        return related if isinstance(related, Book) else None
