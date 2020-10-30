from django.db import models
from django.db.models.signals import pre_delete
from django.urls import reverse

from rard.research.models.mixins import TextObjectFieldMixin
from rard.utils.basemodel import DatedBaseModel


class Antiquarian(TextObjectFieldMixin, DatedBaseModel):

    class Meta:
        ordering = ['name']

    # extend the dates functionality with more detail
    # on what the dates means

    DATES_LIVED = 'lived'
    DATES_ACTIVE = 'active'

    DATES_INFO_CHOICES = [
        (DATES_LIVED, 'Lived'),
        (DATES_ACTIVE, 'Active'),
    ]

    name = models.CharField(max_length=128, blank=False)

    biography = models.OneToOneField(
        'TextObjectField', on_delete=models.SET_NULL, null=True,
        related_name='biography_for'
    )

    re_code = models.CharField(
        max_length=64, blank=False, unique=True, verbose_name='RE Number'
    )

    works = models.ManyToManyField('Work', blank=True)

    fragments = models.ManyToManyField(
        'Fragment', related_name='linked_%(class)ss', blank=True,
        through='FragmentLink'
    )

    testimonia = models.ManyToManyField(
        'Testimonium', related_name='linked_%(class)ss', blank=True,
        through='TestimoniumLink'
    )

    # what the year info means
    dates_type = models.CharField(
        max_length=16,
        choices=DATES_INFO_CHOICES,
        blank=True
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('antiquarian:detail', kwargs={'pk': self.pk})

    def ordered_fragments(self):
        return self.fragments.order_by('antiquarian_fragment_links__order')

    def display_date_range(self):
        return super().display_date_range(
            prepend=self.get_dates_type_display()
        )


def remove_stale_antiquarian_links(sender, instance, **kwargs):
    # any fragment or testimonium links to this antiquarian
    # (and not via a work) should be deleted
    from rard.research.models.base import FragmentLink, TestimoniumLink

    qs = FragmentLink.objects.filter(
        antiquarian=instance, work__isnull=True
    )
    qs.delete()

    qs = TestimoniumLink.objects.filter(
        antiquarian=instance, work__isnull=True
    )
    qs.delete()


pre_delete.connect(remove_stale_antiquarian_links, sender=Antiquarian)


Antiquarian.init_text_object_fields()
