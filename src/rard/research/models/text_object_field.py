from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404
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

    def get_related_object(self):
        # what model instance owns this text object field?
        related_fields = [
            f
            for f in self._meta.get_fields()
            if f.auto_created and not f.concrete and not f.many_to_many
        ]
        for field in related_fields:
            try:
                return getattr(self, field.name)
            except ObjectDoesNotExist:
                pass
        return None

    def update_mentions(self):
        # get the items currently mentioned in the TOF
        found_mention_items = self.get_fragment_testimonia_mentions()

        # iterate through fragment, testimonium and anonymousfragment classes
        for class_name, found_pks in found_mention_items.items():
            # get related queryset
            class_mentions_queryset = getattr(self, class_name + "_mentions")
            for instance in class_mentions_queryset.all():
                print("instance info TOF:", instance.__class__.name, instance.pk, "\n")
                try:
                    get_object_or_404(instance.__class__, pk=instance.pk)
                except Http404:
                    instance.mentioned_in.remove(
                        self
                    )  # if instance no longer exists, remove it from mentioned_in
                if instance.pk not in found_pks:
                    # Fragment instance is no longer mentioned so remove it
                    instance.mentioned_in.remove(self)
                else:
                    # Fragment instance is mentioned so remove from found_pks
                    found_pks.remove(instance.pk)
            # found_pks should now only contain new mentions
            for pk in found_pks:
                try:
                    class_mentions_queryset.add(pk)
                except IntegrityError:
                    pass

    def save(self, *args, **kwargs):
        # Update links generated from mentions each time we save
        self.link_bibliography_mentions_in_content()
        if not self._state.adding:
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

        related = self.get_related_object()
        return related if isinstance(related, Fragment) else None

    @property
    def anonymousfragment(self):
        from rard.research.models import AnonymousFragment

        related = self.get_related_object()
        return related if isinstance(related, AnonymousFragment) else None

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
