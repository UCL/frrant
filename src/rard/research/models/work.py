from itertools import groupby

from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils.text import slugify
from simple_history.models import HistoricalRecords

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
        default="Introduction",
        related_name="introduction_for_%(class)s",
    )
    plain_introduction = models.TextField(blank=False, default="")

    def book_set(self):
        return super().book_set().order_by("unknown", "order", "number")

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

        fragments = list(
            self.antiquarian_work_fragmentlinks.values(
                "definite_antiquarian",
                "definite_work",
                "definite_book",
                "book",
                "order",
                pk=F("fragment__pk"),
                link_id=F("id"),
            ).order_by("book", "order")
        )
        testimonia = list(
            self.antiquarian_work_testimoniumlinks.values(
                "definite_antiquarian",
                "definite_work",
                "definite_book",
                "book",
                "order",
                pk=F("testimonium__pk"),
                link_id=F("id"),
            ).order_by("book", "order")
        )
        apposita = list(
            self.antiquarian_work_appositumfragmentlinks.values(
                "definite_antiquarian",
                "definite_work",
                "definite_book",
                "book",
                "order",
                pk=F("anonymous_fragment__pk"),
                link_id=F("id"),
            ).order_by("book", "order")
        )
        materials = {
            "fragments": (fragments, Fragment),
            "testimonia": (testimonia, Testimonium),
            "apposita": (apposita, AnonymousFragment),
        }
        # need to also add the link id for the move function
        links = {
            "fragments": FragmentLink,
            "testimonia": TestimoniumLink,
            "apposita": AppositumFragmentLink,
        }

        books = self.book_set.all()
        unknown_book = self.unknown_book

        ordered_materials = {book: {} for book in books}

        for material_type, (query_list, model) in materials.items():
            for num, itr in groupby(query_list, lambda x: x["book"]):
                book = books.get(id=num) if num else unknown_book
                content = ordered_materials[book]

                content[material_type] = {
                    links[material_type].objects.get(id=f["link_id"]): {
                        "linked": model.objects.get(id=f["pk"]),
                        "definite_antiquarian": f["definite_antiquarian"],
                        "definite_work": f["definite_work"],
                        "definite_book": f["definite_book"],
                        "order": f["order"],
                    }
                    for f in itr
                }
        return ordered_materials


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
        default="Introduction",
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


@disable_for_loaddata
def create_unknown_book(sender, instance, **kwargs):
    unknown_book = Book.objects.create(
        subtitle="Unknown Book", unknown=True, work=instance
    )
    unknown_book.save()
    instance.book_set.add(unknown_book)


post_save.connect(create_unknown_book, sender=Work)
