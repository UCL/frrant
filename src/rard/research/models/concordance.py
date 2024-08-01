from django.db import models

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel


class PartIdentifier(HistoryModelMixin, BaseModel):
    def __str__(self):
        return f"{self.edition.name}: {self.value}"

    edition = models.ForeignKey("Edition", on_delete=models.CASCADE)
    value = models.CharField(max_length=250, blank=False)
    display_order = models.CharField(max_length=30, blank=True)


class Edition(HistoryModelMixin, BaseModel):
    def __str__(self, bib=False):
        if bib:
            return self.description
        else:
            return f"{self.name} ({self.description})"

    name = models.CharField(max_length=128, blank=False)

    description = models.CharField(
        max_length=200, blank=True, null=True
    )  # need to add this to master bib


class ConcordanceModel(HistoryModelMixin, BaseModel):
    def __str__(self):
        return f"{self.identifier} ({self.content_type}) {self.reference}"

    original_text = models.ForeignKey(
        "OriginalText",
        on_delete=models.CASCADE,
        related_name="concordance_models",
        null=True,
    )

    identifier = models.ForeignKey(
        "PartIdentifier", on_delete=models.SET_NULL, null=True
    )

    TYPE_CHOICES = [
        ("F", "Fragment"),
        ("T", "Testimonium"),
        ("App", "Appendix"),
        ("P.", "Pagination"),
        ("NA", "N/A"),
    ]
    content_type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    reference = models.CharField(max_length=15, blank=True)
    concordance_order = models.CharField(max_length=15, blank=True)

    @property
    def antiquarians(self):
        links = self.original_text.owner.get_all_links()
        aqs = set()
        for link in links:
            if link.antiquarian:
                aqs.add(link.antiquarian)
        return aqs

    @property
    def works(self):
        links = self.original_text.owner.get_all_links()
        works = set()
        for link in links:
            if link.antiquarian:
                works.add(link.antiquarian)
        return works
