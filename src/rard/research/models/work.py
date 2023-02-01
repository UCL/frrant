from itertools import groupby

from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import F
from django.urls import reverse
from django.utils.text import slugify
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel, DatedModel, LockableModel, OrderableModel


class WorkManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        # mark up the queryset with the lowest author name and then
        # order by that followed by name
        # Make sure anonymous works are at the top with nulls_first parameter

        return qs.annotate(
            authors=StringAgg("worklink__antiquarian__order_name", delimiter=",")
        ).order_by(models.F(("authors")).asc(nulls_first=True), "name", "order_year")


class Work(HistoryModelMixin, DatedModel, LockableModel, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self

    class Meta:
        ordering = ["name"]

    objects = WorkManager()

    name = models.CharField(max_length=128, blank=False)

    subtitle = models.CharField(max_length=128, blank=True)

    number_of_books = models.CharField(max_length=128, blank=True)

    # antiquarians = models.ManyToManyField('Antiquarian', blank=True,
    #     through='WorkLink'
    # )

    # @property
    # def antiquarians(self):
    #     from rard.research.models import Antiquarian
    #     return Antiquarian.objects.filter(worklink__work=self).distinct()

    def __str__(self):
        author_str = ", ".join([a.name for a in self.antiquarian_set.all()])
        return "{}: {}".format(author_str or "Anonymous", self.name)

    def get_absolute_url(self):
        return reverse("work:detail", kwargs={"pk": self.pk})

    def all_fragments(self):
        from rard.research.models import Fragment

        links = self.antiquarian_work_fragmentlinks.all()
        return Fragment.objects.filter(antiquarian_fragmentlinks__in=links).distinct()

    def definite_fragments(self):
        from rard.research.models import Fragment

        links = self.antiquarian_work_fragmentlinks.filter(definite=True)
        return Fragment.objects.filter(antiquarian_fragmentlinks__in=links).distinct()

    def possible_fragments(self):
        from rard.research.models import Fragment

        links = self.antiquarian_work_fragmentlinks.filter(definite=False)
        return Fragment.objects.filter(antiquarian_fragmentlinks__in=links).distinct()

    def all_testimonia(self):
        from rard.research.models import Testimonium

        links = self.antiquarian_work_testimoniumlinks.all()
        return Testimonium.objects.filter(
            antiquarian_testimoniumlinks__in=links
        ).distinct()

    def definite_testimonia(self):
        from rard.research.models import Testimonium

        links = self.antiquarian_work_testimoniumlinks.filter(definite=True)
        return Testimonium.objects.filter(
            antiquarian_testimoniumlinks__in=links
        ).distinct()

    def possible_testimonia(self):
        from rard.research.models import Testimonium

        links = self.antiquarian_work_testimoniumlinks.filter(definite=False)
        return Testimonium.objects.filter(
            antiquarian_testimoniumlinks__in=links
        ).distinct()

    def get_ordered_materials(self):
        from rard.research.models import Fragment, Testimonium, AnonymousFragment

        fragments = list(
            self.antiquarian_work_fragmentlinks.values(
                "definite", "book", "order", pk=F("fragment__pk")
            ).order_by("book", "order")
        )
        testimonia = list(
            self.antiquarian_work_testimoniumlinks.values(
                "definite", "book", "order", pk=F("testimonium__pk")
            ).order_by("book", "-definite", "order")
        )
        apposita = list(
            self.antiquarian_work_appositumfragmentlinks.values(
                "definite", "book", "order", pk=F("anonymous_fragment__pk")
            ).order_by("book", "-definite", "order")
        )

        materials = {
            "fragments": (fragments, Fragment),
            "testimonia": (testimonia, Testimonium),
            "apposita": (apposita, AnonymousFragment),
        }

        books = self.book_set.all()
        ordered_materials = {
            book: {material: [] for material in materials.keys()}
            for book in list(books) + ["Unknown Book"]
        }
        grouped_dict = {}

        for material_type in materials.keys():
            query_list = materials[material_type][0]
            model = materials[material_type][1]
            for k, v in groupby(query_list, lambda x: x["book"]):
                if k:
                    b = books.get(id=k)
                else:
                    b = "Unknown Book"
                grouped_dict.setdefault(b, {})
                grouped_dict[b][material_type] = [
                    {
                        "item": model.objects.get(id=f["pk"]),
                        "definite": f["definite"],
                        "order": f["order"],
                    }
                    for f in v
                ]
        for book, material in grouped_dict.items():
            if book:
                ordered_materials[book] = material

            else:  # If book is None it's unknown
                ordered_materials["Unknown Book"] = material

        for type in list(ordered_materials.keys()):
            content = ordered_materials[type]
            has_material = any([bool(item_list) for item_list in content.values()])
            if not has_material:
                del ordered_materials[type]
        return ordered_materials


class Book(HistoryModelMixin, DatedModel, BaseModel, OrderableModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.work

    class Meta:
        ordering = ["order"]

    work = models.ForeignKey("Work", null=False, on_delete=models.CASCADE)

    number = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    subtitle = models.CharField(max_length=128, blank=True)

    def __str__(self):
        if self.subtitle and self.number:
            return "Book {}: {}".format(self.number, self.subtitle)
        elif self.number:
            return "Book {}".format(self.number)
        return self.subtitle

    def related_queryset(self):
        return Book.objects.filter(work=self.work)

    def get_absolute_url(self):
        # link to its owning work
        return reverse("work:detail", kwargs={"pk": self.work.pk})

    def get_display_name(self):
        return self.__str__()

    def get_anchor_id(self):
        return slugify(self.__str__())
