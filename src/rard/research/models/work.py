from django.db import models
from django.urls import reverse

from rard.utils.basemodel import BaseModel, DatedModel, LockableModel


class WorkManager(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset()
        # mark up the queryset with the lowest author name and then
        # order by that
        return qs.annotate(
            authors=models.Min('antiquarian__name')
        ).order_by('authors')


class Work(DatedModel, LockableModel, BaseModel):

    class Meta:
        ordering = ['name']

    objects = WorkManager()

    name = models.CharField(max_length=128, blank=False)

    subtitle = models.CharField(max_length=128, blank=True)

    number_of_books = models.CharField(max_length=128, blank=True)

    def __str__(self):
        author_str = ', '.join([a.name for a in self.antiquarian_set.all()])
        return '{}: {}'.format(author_str or 'Anonymous', self.name)

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

    def definite_testimonia(self):
        from rard.research.models import Testimonium
        links = self.antiquarian_work_testimonium_links.filter(definite=True)
        return Testimonium.objects.filter(
            antiquarian_testimonium_links__in=links
        ).distinct()

    def possible_testimonia(self):
        from rard.research.models import Testimonium
        links = self.antiquarian_work_testimonium_links.filter(definite=False)
        return Testimonium.objects.filter(
            antiquarian_testimonium_links__in=links
        ).distinct()


class Book(DatedModel, BaseModel):

    class Meta:
        ordering = ['number']

    work = models.ForeignKey(
        'Work',
        null=False,
        on_delete=models.CASCADE
    )

    number = models.PositiveSmallIntegerField(
        default=None, null=True, blank=True
    )
    subtitle = models.CharField(max_length=128, blank=True)

    def __str__(self):
        if self.subtitle and self.number:
            return 'Book {}: {}'.format(self.number, self.subtitle)
        elif self.number:
            return 'Book {}'.format(self.number)
        return self.subtitle

    def get_absolute_url(self):
        # link to its owning work
        return reverse('work:detail', kwargs={'pk': self.work.pk})
