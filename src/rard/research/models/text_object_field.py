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

    def get_history_title(self):
        obj = self.get_related_object()
        if obj.__class__.__name__ in ["Antiquarian", "Work", "Book"]:
            return "Introduction"
        return "Commentary"

    def __str__(self):
        return self.content

    def get_related_object(self, exclude_properties=False):
        # what model instance owns this text object field?
        related_fields = [
            f for f in self._meta.get_fields() if f.auto_created and not f.concrete
        ]
        for field in related_fields:
            if exclude_properties and field.name in [
                "fragment",
                "anonymousfragment",
                "work",
                "book",
                "testimonium",
                "antiquarian",
            ]:
                continue
            try:
                return getattr(self, field.name)
            except ObjectDoesNotExist:
                pass
        return None

    fragment_testimonia_mentions = []

    def update_mentions(self):
        # get the items currently mentioned in the TOF
        found_mention_items = self.get_fragment_testimonia_mentions()
        # Compare the list of currently found to previously found items and if they differ, update
        if self.fragment_testimonia_mentions != found_mention_items:
            items_to_remove = [
                item
                for item in self.fragment_testimonia_mentions
                if item not in found_mention_items
            ]

            return self.set_fragment_testimonia_mentions(
                found_mention_items, items_to_remove
            )

    def set_fragment_testimonia_mentions(self, to_set, to_remove):
        for item in self.fragment_testimonia_mentions:
            if item in to_remove:
                item.mentioned_in.remove(self)
                self.fragment_testimonia_mentions.remove(item)

        for item in to_set:
            item.mentioned_in.add(self)  # add this TOF to the item found via m2m
            self.fragment_testimonia_mentions.append(
                item
            )  # add the found object to the list
        return self.fragment_testimonia_mentions

    def save(self, *args, **kwargs):
        # Update links generated from mentions each time we save
        self.link_bibliography_mentions_in_content()
        self.update_mentions()

        # save the parent object so the plain intro/commentary is
        # updated for search purposes.
        obj = self.get_related_object()
        if obj:
            obj.save()
        super().save(*args, **kwargs)

    @property
    def fragment(self):
        from rard.research.models import Fragment

        related = self.get_related_object(exclude_properties=True)
        return related if isinstance(related, Fragment) else None

    @property
    def anonymousfragment(self):
        from rard.research.models import AnonymousFragment

        related = self.get_related_object(exclude_properties=True)
        return related if isinstance(related, AnonymousFragment) else None

    @property
    def testimonium(self):
        from rard.research.models import Testimonium

        related = self.get_related_object(exclude_properties=True)
        return related if isinstance(related, Testimonium) else None

    @property
    def antiquarian(self):
        from rard.research.models import Antiquarian

        related = self.get_related_object(exclude_properties=True)
        return related if isinstance(related, Antiquarian) else None

    @property
    def work(self):
        from rard.research.models import Work

        related = self.get_related_object(exclude_properties=True)
        return related if isinstance(related, Work) else None

    @property
    def book(self):
        from rard.research.models import Book

        related = self.get_related_object(exclude_properties=True)
        return related if isinstance(related, Book) else None
