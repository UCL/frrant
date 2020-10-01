from django.db import models

from rard.research.mixins import TextObjectFieldMixin
from rard.utils.basemodel import BaseModel


class HistoricalBaseModel(TextObjectFieldMixin, BaseModel):

    # abstract base class for shared properties of fragments and testimonia
    class Meta:
        abstract = True
        ordering = ['name']

    name = models.CharField(max_length=128, blank=False, unique=True)

    apparatus_criticus = models.TextField(default='', blank=True)

    commentary = models.OneToOneField(
        'TextObjectField', on_delete=models.SET_NULL, null=True,
        # related_name='commentary_for',
        related_name="commentary_for_%(class)s",
        blank=True,
    )

    images = models.ManyToManyField('Image', blank=True)

    definite_works = models.ManyToManyField(
        'Work', related_name='definite_%(class)ss', blank=True
    )
    possible_works = models.ManyToManyField(
        'Work', related_name='possible_%(class)ss', blank=True
    )

    definite_antiquarians = models.ManyToManyField(
        'Antiquarian', related_name='definite_%(class)ss', blank=True
    )
    possible_antiquarians = models.ManyToManyField(
        'Antiquarian', related_name='possible_%(class)ss', blank=True
    )

    images = models.ManyToManyField('Image', blank=True)

    def __str__(self):
        return self.name

    def get_detail_url(self):  # pragma: no cover
        class_name = self.__class__.__name__
        raise NotImplementedError(
            '%s must provide a get_detail_url() method' % class_name
        )
