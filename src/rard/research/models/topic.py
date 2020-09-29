from django.db import models
from django.utils.text import slugify

from rard.utils.basemodel import BaseModel


class Topic(BaseModel):

    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=128, blank=False, unique=True)

    slug = models.SlugField(max_length=128)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
