from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse

from .base import HistoricalBaseModel, TestimoniumLink


class Testimonium(HistoricalBaseModel):

    original_texts = GenericRelation(
        'OriginalText', related_query_name='original_texts'
    )

    def definite_works(self):
        from rard.research.models import Work
        all_links = self.antiquarian_testimonium_links.all()
        return Work.objects.filter(
            antiquarian_work_testimonium_links__in=all_links,
            antiquarian_work_testimonium_links__definite=True,
            antiquarian_work_testimonium_links__work__isnull=False,
        ).distinct()

    def possible_works(self):
        from rard.research.models import Work
        all_links = self.antiquarian_testimonium_links.all()
        return Work.objects.filter(
            antiquarian_work_testimonium_links__in=all_links,
            antiquarian_work_testimonium_links__definite=False,
            antiquarian_work_testimonium_links__work__isnull=False,
        ).distinct()

    def definite_antiquarians(self):
        from rard.research.models import Antiquarian
        return Antiquarian.objects.filter(
            testimoniumlinks__in=self.antiquarian_testimonium_links.all(),
            testimoniumlinks__definite=True,
            testimoniumlinks__work__isnull=True,
        ).distinct()

    def possible_antiquarians(self):
        from rard.research.models import Antiquarian
        return Antiquarian.objects.filter(
            testimoniumlinks__in=self.antiquarian_testimonium_links.all(),
            testimoniumlinks__definite=False,
            testimoniumlinks__work__isnull=True,
        ).distinct()

    def get_absolute_url(self):
        return reverse('testimonium:detail', kwargs={'pk': self.pk})

    def get_all_names(self):
        return [
            link.get_display_name()
            for link in TestimoniumLink.objects.filter(
                testimonium=self
            ).order_by('antiquarian', 'order').distinct()
        ]


Testimonium.init_text_object_fields()
