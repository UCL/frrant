from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse

from rard.research.models.base import FragmentLink, HistoricalBaseModel


class Fragment(HistoricalBaseModel):

    # fragments can also have topics
    topics = models.ManyToManyField('Topic', blank=True)

    original_texts = GenericRelation(
        'OriginalText', related_query_name='original_texts'
    )

    def definite_works(self):
        from rard.research.models import Work
        all_links = self.antiquarian_fragment_links.all()
        return Work.objects.filter(
            antiquarian_work_fragment_links__in=all_links,
            antiquarian_work_fragment_links__definite=True,
            antiquarian_work_fragment_links__work__isnull=False,
        ).distinct()

    def possible_works(self):
        from rard.research.models import Work
        all_links = self.antiquarian_fragment_links.all()
        return Work.objects.filter(
            antiquarian_work_fragment_links__in=all_links,
            antiquarian_work_fragment_links__definite=False,
            antiquarian_work_fragment_links__work__isnull=False,
        ).distinct()

    def definite_antiquarians(self):
        from rard.research.models import Antiquarian
        return Antiquarian.objects.filter(
            fragmentlinks__in=self.antiquarian_fragment_links.all(),
            fragmentlinks__definite=True,
            fragmentlinks__work__isnull=True,
        ).distinct()

    def possible_antiquarians(self):
        from rard.research.models import Antiquarian
        return Antiquarian.objects.filter(
            fragmentlinks__in=self.antiquarian_fragment_links.all(),
            fragmentlinks__definite=False,
            fragmentlinks__work__isnull=True,
        ).distinct()

    def get_absolute_url(self):
        return reverse('fragment:detail', kwargs={'pk': self.pk})

    def get_all_names(self):
        return [
            link.get_display_name()
            for link in FragmentLink.objects.filter(
                fragment=self
            ).order_by('antiquarian', 'order').distinct()
        ]


Fragment.init_text_object_fields()
