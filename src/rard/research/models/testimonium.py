from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse

from .base import HistoricalBaseModel, TestimoniumLink


class Testimonium(HistoricalBaseModel):

    original_texts = GenericRelation(
        'OriginalText', related_query_name='original_texts'
    )

    def _get_linked_works_and_books(self, definite):
        # a list of definite linked works and books
        all_links = self.antiquarian_testimonium_links.filter(
            definite=definite,
            work__isnull=False,
        ).order_by('work', '-book').distinct()

        rtn = set()
        for link in all_links:
            if link.book:
                rtn.add(link.book)
            else:
                rtn.add(link.work)
        return rtn

    def possible_works_and_books(self):
        return self._get_linked_works_and_books(definite=False)

    def definite_works_and_books(self):
        return self._get_linked_works_and_books(definite=True)

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
