from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel, DatedModel, LockableModel


class CitingAuthor(HistoryModelMixin, LockableModel, DatedModel, BaseModel):
    class Meta:
        ordering = ("order_name",)

    name = models.CharField(max_length=256, blank=False)

    order_name = models.CharField(
        max_length=128,
        default="",
        blank=True,
    )

    history = HistoricalRecords(excluded_fields=[])

    ANONYMOUS_ORDERNAME = "anonymous_citing_author_order_name"

    bibliography_items = models.ManyToManyField(
        "BibliographyItem", related_name="citing_authors", blank=True
    )

    @classmethod
    def get_anonymous_citing_author(cls):
        return cls.objects.get_or_create(
            name="Anonymous", order_name=cls.ANONYMOUS_ORDERNAME
        )[0]

    def get_absolute_url(self):
        return reverse("citingauthor:detail", kwargs={"pk": self.pk})

    def related_lock_object(self):
        return self

    def __str__(self):
        return self.name or "Unnamed Author"

    def is_anonymous_citing_author(self):
        # are we the special database record reserved for the
        # anonymous citing author?
        return self.order_name == self.ANONYMOUS_ORDERNAME

    def ordered_materials(self):
        # for all (or a page of) links to materials we need to create a
        # dict for display on the page. Fetch all and order in a dict
        # is probably faster than a set of individual db queries
        from rard.research.models import AnonymousFragment, Fragment, Testimonium

        ordering = [
            "original_texts__citing_work",  # Group by work
            "original_texts__reference_order",  # Then order by reference order
        ]
        testimonia = (
            Testimonium.objects.filter(original_texts__citing_work__author=self)
            .order_by(*ordering)
            .distinct()
        )
        fragments = (
            Fragment.objects.filter(original_texts__citing_work__author=self)
            .order_by(*ordering)
            .distinct()
        )
        apposita = (
            AnonymousFragment.objects.filter(original_texts__citing_work__author=self)
            .order_by(*ordering)
            .distinct()
        )
        return {"testimonia": testimonia, "fragments": fragments, "apposita": apposita}

    def save(self, *args, **kwargs):
        if not self.order_name:
            self.order_name = self.name
        super().save(*args, **kwargs)


class CitingWork(HistoryModelMixin, LockableModel, DatedModel, BaseModel):

    history = HistoricalRecords(excluded_fields=[])

    def related_lock_object(self):
        return self

    # allow blank name as may be anonymous
    author = models.ForeignKey(
        "CitingAuthor",
        on_delete=models.SET(CitingAuthor.get_anonymous_citing_author),
        default=None,
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=256, blank=False)

    edition = models.CharField(max_length=128, blank=True)

    def get_absolute_url(self):
        return reverse("citingauthor:work_detail", kwargs={"pk": self.pk})

    def __str__(self):
        tokens = [str(self.author) if self.author else _("Anonymous"), self.title]
        return ", ".join([t for t in tokens if t])

    def fragments(self):
        from rard.research.models import Fragment

        return Fragment.objects.filter(original_texts__citing_work=self).distinct()

    def testimonia(self):
        from rard.research.models import Testimonium

        return Testimonium.objects.filter(original_texts__citing_work=self).distinct()

    def apposita(self):
        from rard.research.models import AnonymousFragment

        return AnonymousFragment.objects.filter(
            original_texts__citing_work=self
        ).distinct()

    def save(self, *args, **kwargs):
        if not self.author:
            self.author = CitingAuthor.get_anonymous_citing_author()
        super().save(*args, **kwargs)
