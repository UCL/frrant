from itertools import chain, groupby

from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.urls import reverse
from django.utils.text import slugify
from simple_history.models import HistoricalRecords

from rard.research.models.base import (
    AppositumFragmentLink,
    FragmentLink,
    TestimoniumLink,
)
from rard.research.models.mixins import HistoryModelMixin, TextObjectFieldMixin
from rard.utils.basemodel import BaseModel, DatedModel, LockableModel, OrderableModel
from rard.utils.decorators import disable_for_loaddata
from rard.utils.text_processors import make_plain_text


class WorkManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        # mark up the queryset with the lowest author name and then
        # order by that followed by name
        # Make sure anonymous works are at the top with nulls_first parameter

        return qs.annotate(
            authors=StringAgg("worklink__antiquarian__order_name", delimiter=",")
        ).order_by(models.F(("authors")).asc(nulls_first=True), "name", "order_year")


class Work(
    HistoryModelMixin, TextObjectFieldMixin, DatedModel, LockableModel, BaseModel
):
    history = HistoricalRecords()

    def related_lock_object(self):
        return self

    class Meta:
        ordering = ["name"]

    objects = WorkManager()

    name = models.CharField(max_length=128, blank=False)

    subtitle = models.CharField(max_length=128, blank=True)

    number_of_books = models.CharField(max_length=128, blank=True)

    unknown = models.BooleanField(default=False)

    introduction = models.OneToOneField(
        "TextObjectField",
        on_delete=models.SET_NULL,
        null=True,
        related_name="introduction_for_%(class)s",
    )
    plain_introduction = models.TextField(blank=False, default="")

    @property
    def unknown_book(self):
        return self.book_set.filter(unknown=True).first()

    # @property
    # def antiquarians(self):
    #     from rard.research.models import Antiquarian
    #     return Antiquarian.objects.filter(worklink__work=self).distinct()

    def __str__(self):
        author_str = ", ".join([a.name for a in self.antiquarian_set.all()])
        return "{}: {}".format(author_str or "Anonymous", self.name)

    def save(self, *args, **kwargs):
        if self.introduction:
            self.plain_introduction = make_plain_text(self.introduction.content)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("work:detail", kwargs={"pk": self.pk})

    def all_fragments(self):
        from rard.research.models import Fragment

        links = self.antiquarian_work_fragmentlinks.all()
        return Fragment.objects.filter(antiquarian_fragmentlinks__in=links).distinct()

    def definite_fragments(self):
        from rard.research.models import Fragment

        links = self.antiquarian_work_fragmentlinks.filter(definite_work=True)
        return Fragment.objects.filter(antiquarian_fragmentlinks__in=links).distinct()

    def possible_fragments(self):
        from rard.research.models import Fragment

        links = self.antiquarian_work_fragmentlinks.filter(definite_work=False)
        return Fragment.objects.filter(antiquarian_fragmentlinks__in=links).distinct()

    def all_testimonia(self):
        from rard.research.models import Testimonium

        links = self.antiquarian_work_testimoniumlinks.all()
        return Testimonium.objects.filter(
            antiquarian_testimoniumlinks__in=links
        ).distinct()

    def definite_testimonia(self):
        from rard.research.models import Testimonium

        links = self.antiquarian_work_testimoniumlinks.filter(definite_work=True)
        return Testimonium.objects.filter(
            antiquarian_testimoniumlinks__in=links
        ).distinct()

    def possible_testimonia(self):
        from rard.research.models import Testimonium

        links = self.antiquarian_work_testimoniumlinks.filter(definite_work=False)
        return Testimonium.objects.filter(
            antiquarian_testimoniumlinks__in=links
        ).distinct()

    def get_ordered_materials(self):
        from rard.research.models import AnonymousFragment, Fragment, Testimonium
        from rard.research.models.base import (
            AppositumFragmentLink,
            FragmentLink,
            TestimoniumLink,
        )

        fragment_links = list(
            self.antiquarian_work_fragmentlinks.values(
                "definite_antiquarian",
                "definite_work",
                "definite_book",
                "book",
                "order_in_book",
                pk=F("fragment__pk"),
                link_id=F("id"),
            ).order_by("book", "order_in_book")
        )
        testimonium_links = list(
            self.antiquarian_work_testimoniumlinks.values(
                "definite_antiquarian",
                "definite_work",
                "definite_book",
                "book",
                "order_in_book",
                pk=F("testimonium__pk"),
                link_id=F("id"),
            ).order_by("book", "order_in_book")
        )
        appositum_links = list(
            self.antiquarian_work_appositumfragmentlinks.values(
                "definite_antiquarian",
                "definite_work",
                "definite_book",
                "book",
                "order_in_book",
                pk=F("anonymous_fragment__pk"),
                link_id=F("id"),
            ).order_by("book", "order_in_book")
        )
        materials = {
            "fragments": (fragment_links, Fragment, FragmentLink),
            "testimonia": (testimonium_links, Testimonium, TestimoniumLink),
            "apposita": (appositum_links, AnonymousFragment, AppositumFragmentLink),
        }

        books = self.book_set.all()  # Unknown should be last by default

        ordered_materials = {book: {} for book in books}

        for material_type, (query_list, model, link_model) in materials.items():
            for book_id, links in groupby(query_list, lambda x: x["book"]):
                book = books.get(id=book_id)
                content = ordered_materials[book]

                content[material_type] = {
                    link_model.objects.get(id=link["link_id"]): {
                        "linked": model.objects.get(id=link["pk"]),
                        "definite_antiquarian": link["definite_antiquarian"],
                        "definite_work": link["definite_work"],
                        "definite_book": link["definite_book"],
                        "order": link["order_in_book"],
                    }
                    for link in links
                }
        return ordered_materials

    def reindex_related_links(self):
        """When links are reordered within a book, or the order of books
        changes with respect to this work, we need to recalculate work_order
        for each FragmentLink, TestimoniumLink and AppositumFragmentLink.
        Then call equivalent reindex_fragment_and_testimonium_links method
        on the related Antiquarian"""

        from django.db import transaction

        with transaction.atomic():
            to_reorder = [
                FragmentLink.objects.filter(work=self).order_by(
                    "book__unknown", "book__order", "order_in_book"
                ),
                TestimoniumLink.objects.filter(work=self).order_by(
                    "book__unknown", "book__order", "order_in_book"
                ),
                AppositumFragmentLink.objects.filter(work=self).order_by(
                    "book__unknown", "book__order", "order_in_book"
                ),
            ]

            for qs in to_reorder:
                for count, link in enumerate(qs):
                    if link.work_order != count:
                        link.work_order = count
                        link.save()

        # There should only ever be one antiquarian, but no harm in covering all eventualities
        for antiquarian in self.antiquarian_set.all():
            antiquarian.reindex_fragment_and_testimonium_links()


class Book(
    HistoryModelMixin, TextObjectFieldMixin, DatedModel, BaseModel, OrderableModel
):
    history = HistoricalRecords()

    def related_lock_object(self):
        return self.work

    class Meta:
        ordering = ["unknown", "order", "number"]

    work = models.ForeignKey("Work", null=False, on_delete=models.CASCADE)

    number = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    subtitle = models.CharField(max_length=128, blank=True)

    unknown = models.BooleanField(default=False)

    introduction = models.OneToOneField(
        "TextObjectField",
        on_delete=models.SET_NULL,
        null=True,
        related_name="introduction_for_%(class)s",
    )
    plain_introduction = models.TextField(blank=False, default="")

    def __str__(self):
        if self.subtitle and self.number:
            return "Book {}: {}".format(self.number, self.subtitle)
        elif self.number:
            return "Book {}".format(self.number)
        return self.subtitle

    def related_queryset(self):
        return Book.objects.filter(work=self.work).exclude(unknown=True)

    def get_absolute_url(self):
        # link to its owning work
        return reverse("work:detail", kwargs={"pk": self.work.pk})

    def get_display_name(self):
        return self.__str__()

    def get_anchor_id(self):
        return slugify(self.__str__())

    def save(self, *args, **kwargs):
        if self.introduction:
            self.plain_introduction = make_plain_text(self.introduction.content)
        super().save(*args, **kwargs)

    def reindex_related_links(self):
        """Following a change, ensure all links to this book have a distinct
        zero-indexed order in this book."""
        to_reorder = [
            self.antiquarian_book_fragmentlinks.all().order_by("order_in_book"),
            self.antiquarian_book_testimoniumlinks.all().order_by("order_in_book"),
            self.antiquarian_book_appositumfragmentlinks.all().order_by(
                "order_in_book"
            ),
        ]

        for qs in to_reorder:
            for count, link in enumerate(qs):
                if link.order_in_book != count:
                    link.order_in_book = count
                    link.save()


@disable_for_loaddata
def create_unknown_book(sender, instance, **kwargs):
    if not instance.unknown_book:
        unknown_book = Book.objects.create(
            subtitle="Unknown Book", unknown=True, work=instance
        )
        # call function to make sure unknown book contents are collated
        unknown_book.save()


@disable_for_loaddata
def handle_reordered_books(sender, instance, **kwargs):
    # reindex links for antiquarian
    instance.work.reindex_related_links()


@disable_for_loaddata
def handle_deleted_book(sender, instance, **kwargs):
    """When a book is deleted, any links should be updated to point to
    the work's unknown book. If however the whole work is being deleted,
    and this is the result of a cascade, we want to do nothing.
    
    We can check this by seeing if the work has an unknown book. It should
    only not have an unknown book in the event that we're part way through
    deleting the work."""
    if not instance.unknown:
        work = instance.work
        if work.unknown_book:
            related_links = chain(
                work.antiquarian_work_fragmentlinks.all(),
                work.antiquarian_work_testimoniumlinks.all(),
                work.antiquarian_work_appositumfragmentlinks.all(),
            )
            for link in related_links:
                if link.book is None:
                    link.book = link.work.unknown_book
                    link.save()
        
            work.unknown_book.reindex_related_links()
            work.reindex_related_links()


post_save.connect(create_unknown_book, sender=Work)
Work.init_text_object_fields()
Book.init_text_object_fields()
post_save.connect(handle_reordered_books, sender=Book)
post_delete.connect(handle_deleted_book, sender=Book)
