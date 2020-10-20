from django.db import models
from django.urls import reverse

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

    def get_absolute_url(self):
        return reverse('work:detail', kwargs={'pk': self.pk})

    def definite_fragments(self):
        from rard.research.models import Fragment
        links = self.antiquarian_work_fragment_links.filter(definite=True)
        return Fragment.objects.filter(
            antiquarian_fragment_links__in=links
        ).distinct()

    def possible_fragments(self):
        from rard.research.models import Fragment
        links = self.antiquarian_work_fragment_links.filter(definite=False)
        return Fragment.objects.filter(
            antiquarian_fragment_links__in=links
        ).distinct()
