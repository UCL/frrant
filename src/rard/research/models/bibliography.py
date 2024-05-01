import re

from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel, LockableModel


class BibliographyItem(HistoryModelMixin, LockableModel, BaseModel):
    history = HistoricalRecords()

    def related_lock_object(self):
        # overrides HistoryModelMixin.related_lock_object
        return self

    def __str__(self):
        r = self.author_surnames
        if self.year:
            r += " [" + self.year + "]"
        title = re.sub(r"<[^>]*>", " ", self.title)
        return r + ": " + re.sub(r"\s+", " ", title).strip()

    def get_absolute_url(self):
        return reverse("bibliography:detail", kwargs={"pk": self.pk})

    def mention_citation(self):
        r = self.author_surnames
        if self.year:
            r += " [" + self.year + "]"
        return r.strip()

    class Meta:
        ordering = ["author_surnames", "year"]

    # string containing names of authors
    # e.g. Smith P, Jones M
    # ordering will be done on this field
    authors = models.CharField(max_length=512, blank=False)

    # comma-separated list of surnames of the authors, to be used for
    # ordering the entries in the list
    author_surnames = models.CharField(
        max_length=512,
        default="",
        blank=False,
        help_text="Comma-separated list of surnames to be used for ordering",
    )

    year = models.CharField(
        max_length=512,
        default="",
        blank=True,
        help_text="Optional date info to use for second-order " "sorting e.g. 1500a",
    )

    title = models.TextField(default="", blank=False)
