from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin

from .base import HistoricalBaseModel, TestimoniumLink


class Testimonium(HistoryModelMixin, HistoricalBaseModel):

    history = HistoricalRecords(
        excluded_fields=[
            'original_texts',
        ]
    )

    def related_lock_object(self):
        return self

    LINK_TYPE = TestimoniumLink

    original_texts = GenericRelation(
        'OriginalText', related_query_name='testimonia'
    )

    def definite_work_and_book_links(self):
        return self.antiquarian_testimoniumlinks.filter(
            definite=True,
            work__isnull=False,
        ).order_by('work', '-book').distinct()

    def possible_work_and_book_links(self):
        return self.antiquarian_testimoniumlinks.filter(
            definite=False,
            work__isnull=False,
        ).order_by('work', '-book').distinct()

    def definite_antiquarian_links(self):
        return self.antiquarian_testimoniumlinks.filter(
            definite=True,
            work__isnull=True
        )

    def possible_antiquarian_links(self):
        return self.antiquarian_testimoniumlinks.filter(
            definite=False,
            work__isnull=True
        )

    def get_absolute_url(self):
        return reverse('testimonium:detail', kwargs={'pk': self.pk})

    def get_all_names(self):
        return [
            link.get_display_name()
            for link in self.get_all_links()
            # for link in self.get_all_links().order_by(
            #     'antiquarian', 'order'
            # ).distinct()
        ]

    def get_all_work_names(self):
        # all the names wrt works
        return [
            link.get_work_display_name()
            for link in self.get_all_links()
            # # for link in self.get_all_links().order_by(
            # #     'work', 'work_order'
            # ).distinct()
        ]

    def get_all_links(self):
        return TestimoniumLink.objects.filter(
            testimonium=self
        ).order_by('antiquarian', 'order').distinct()


Testimonium.init_text_object_fields()
