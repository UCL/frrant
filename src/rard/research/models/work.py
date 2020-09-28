from django.db import models

from rard.utils.basemodel import BaseModel


class Work(BaseModel):

    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=128, blank=False)

    subtitle = models.CharField(max_length=128, blank=True)

    number_of_volumes = models.PositiveSmallIntegerField(
        default=None, null=True, blank=True
    )

    def __str__(self):
        author_str = ', '.join([a.name for a in self.antiquarian_set.all()])
        return '{}: {}'.format(self.name, author_str or 'Anonymous')
