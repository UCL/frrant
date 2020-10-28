from django.db import models
from django.db.models.signals import pre_delete
from django.urls import reverse

from rard.research.mixins import TextObjectFieldMixin
from rard.utils.basemodel import BaseModel


class Antiquarian(TextObjectFieldMixin, BaseModel):

    YEAR_RANGE = 'range'
    YEAR_BEFORE = 'before'
    YEAR_AFTER = 'after'
    YEAR_SINGLE = 'single'

    YEAR_INFO_CHOICES = [
        (YEAR_RANGE, 'From/To'),
        (YEAR_BEFORE, 'Before'),
        (YEAR_AFTER, 'After'),
        (YEAR_SINGLE, 'Single Year'),
    ]

    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=128, blank=False)

    biography = models.OneToOneField(
        'TextObjectField', on_delete=models.SET_NULL, null=True,
        related_name='biography_for'
    )

    re_code = models.CharField(
        max_length=64, blank=False, unique=True, verbose_name='RE Number'
    )

    # negative means BC, positive is AD
    # the meaning of year1 and year depends on type of date info we have
    year1 = models.IntegerField(default=None, null=True, blank=True)
    year2 = models.IntegerField(default=None, null=True, blank=True)
    circa = models.BooleanField(default=False)

    # the type of year info we have
    year_type = models.CharField(
        max_length=16,
        choices=YEAR_INFO_CHOICES,
        blank=True
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

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('antiquarian:detail', kwargs={'pk': self.pk})

    def ordered_fragments(self):
        return self.fragments.order_by('antiquarian_fragment_links__order')

    @classmethod
    def _bcad(cls, year):
        try:
            if year < 0:
                return '{} BC'.format(abs(year))
            else:
                return '{} AD'.format(abs(year))
        except TypeError:
            return ''

    def display_date_range(self):
        if not self.year_type:
            return ''

        if self.year_type == self.YEAR_RANGE:
            if self.year1 * self.year2 < 0:
                # they are of different sides of zero AD
                # so show BC or AD on both
                display_year1 = self._bcad(self.year1)
            else:
                display_year1 = str(abs(self.year1))

            display_year2 = self._bcad(self.year2)

            info = ' to '.join([display_year1, display_year2])
            stub = 'c. ' if self.circa else 'From '
            return stub + info

        else:
            if self.year_type == self.YEAR_SINGLE:
                stub = ''
            else:
                stub = self.get_year_type_display()

            circa = 'c. ' if self.circa else ''
            return '{} {}{}'.format(
                stub, circa, self._bcad(self.year1)
            ).strip()


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
