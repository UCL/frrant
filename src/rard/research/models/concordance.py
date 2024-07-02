from django.db import models

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel


class PartIdentifier(HistoryModelMixin, BaseModel):
    edition = models.ForeignKey("Edition", on_delete=models.CASCADE)
    value = models.CharField(max_length=128, blank=False)


class Edition(HistoryModelMixin, BaseModel):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=128, blank=False)
    display_order = models.CharField(max_length=30, blank=True)


class ConcordanceModel(HistoryModelMixin, BaseModel):
    edition = models.ForeignKey("Edition", on_delete=models.SET_NULL, null=True)

    TYPE_CHOICES = [
        ("F", "Fragment"),
        ("T", "Testimonium"),
        ("App", "Appendix"),
        ("P.", "Pagination"),
        ("NA", "N/A"),
    ]
    content_type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    reference = models.CharField(max_length=15, blank=True)
    concordance_order = models.CharField(
        max_length=15
    )  # maybe add a validator so only numbers and . allowed?
