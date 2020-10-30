from django.db import models
from model_utils.models import TimeStampedModel


class BaseModel(TimeStampedModel, models.Model):

    # defines a base model with any required
    # additional common functionality
    class Meta:
        abstract = True


class DatedBaseModel(BaseModel):
    # for models that have a date range or value, such as
    # antiquarians, works and books

    class Meta:
        abstract = True

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

    # negative means BC, positive is AD
    # the meaning of year1 and year depends on type of date info we have
    year1 = models.IntegerField(default=None, null=True, blank=True)
    year2 = models.IntegerField(default=None, null=True, blank=True)
    circa1 = models.BooleanField(default=False)
    circa2 = models.BooleanField(default=False)

    # the type of year info we have
    year_type = models.CharField(
        max_length=16,
        choices=YEAR_INFO_CHOICES,
        blank=True
    )

    @classmethod
    def _bcad(cls, year):
        try:
            if year < 0:
                return '{} BC'.format(abs(year))
            else:
                return '{} AD'.format(abs(year))
        except TypeError:
            return ''

    def display_date_range(self, prepend=None):
        if not self.year_type:
            return ''

        if self.year_type == self.YEAR_RANGE:
            if self.year1 * self.year2 < 0:
                # they are of different sides of zero AD
                # so show BC or AD on both
                display_year1 = self._bcad(self.year1)
            else:
                display_year1 = str(abs(self.year1))

            if self.circa1:
                display_year1 = 'c. ' + display_year1

            display_year2 = self._bcad(self.year2)

            if self.circa2:
                display_year2 = 'c. ' + display_year2

            info = ' to '.join([display_year1, display_year2])
            return (
                '{} from {}'.format(prepend, info) if prepend
                else 'From {}'.format(info)
            )
        else:
            if self.year_type == self.YEAR_SINGLE:
                stub = ''
            else:
                stub = self.get_year_type_display()
                if prepend:
                    stub = stub.lower()

            circa1 = 'c. ' if self.circa1 else ''
            info = '{} {}{}'.format(
                stub,
                circa1,
                self._bcad(self.year1)
            ).strip()

            return '{} {}'.format(prepend, info) if prepend else info
