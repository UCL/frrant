from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryViewMixin
from rard.utils.basemodel import BaseModel, LockableModel, OrderableModel


class Topic(HistoryViewMixin, OrderableModel, LockableModel, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self

    # class Meta:
    #     ordering = ['order']

    name = models.CharField(max_length=128, blank=False, unique=True)

    slug = models.SlugField(max_length=128)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('topic:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name) or self.slug
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = str(self.pk)
            self.save()

    @property
    def fragments(self):
        # ordered
        return self.fragment_set.all().order_by('topiclink__order')

    def reindex_fragment_links(self):
        # where there has been a change, ensure the
        # ordering of fragments is correct (zero-indexed)
        from django.db import transaction

        from rard.research.models.fragment import TopicLink

        # single db update
        with transaction.atomic():
            links = TopicLink.objects.filter(
                topic=self).order_by(
                    models.F(('order')).asc(nulls_first=False))
            for count, link in enumerate(links):
                link.order = count
                link.save()
