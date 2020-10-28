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

    def _get_linked_works_and_volumes(self, definite):
        # a list of definite linked works and volumes
        all_links = self.antiquarian_fragment_links.filter(
            definite=definite,
            work__isnull=False,
        ).order_by('work', '-volume').distinct()

        rtn = set()
        for link in all_links:
            if link.volume:
                rtn.add(link.volume)
            else:
                rtn.add(link.work)
        return rtn

    def possible_works_and_volumes(self):
        return self._get_linked_works_and_volumes(definite=False)

    def definite_works_and_volumes(self):
        return self._get_linked_works_and_volumes(definite=True)

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
