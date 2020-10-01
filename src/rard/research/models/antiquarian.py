from django.db import models
from django.urls import reverse

from rard.research.mixins import TextObjectFieldMixin
from rard.utils.basemodel import BaseModel


class Antiquarian(TextObjectFieldMixin, BaseModel):

    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=128, blank=False)

    biography = models.OneToOneField(
        'TextObjectField', on_delete=models.SET_NULL, null=True,
        related_name='biography_for'
    )

    re_code = models.CharField(
        max_length=64, blank=False, unique=True
    )

    works = models.ManyToManyField('Work', blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('antiquarian:detail', kwargs={'pk': self.pk})


Antiquarian.init_text_object_fields()
