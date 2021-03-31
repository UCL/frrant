from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.basemodel import BaseModel, DynamicTextField


class OriginalText(HistoryModelMixin, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.owner

    class Meta:
        ordering = ('citing_work', 'reference')

    # original text can belong to either a fragment or a testimonium
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey()

    citing_work = models.ForeignKey('CitingWork', on_delete=models.CASCADE)

    # e.g. page 24
    reference = models.CharField(max_length=128, blank=False)

    content = DynamicTextField(blank=False)

    # to be nuked. not required now
    # apparatus_criticus = DynamicTextField(default='', blank=True)

    apparatus_criticus_items = GenericRelation(
        'ApparatusCriticusItem', related_query_name='original_text'
    )

    def apparatus_criticus_lines(self):
        # use this rather than the above as that doesn't automatically
        # sort the results :/
        return self.apparatus_criticus_items.all().order_by('order')

    def citing_work_reference_display(self):
        citing_work_str = str(self.citing_work)
        if self.reference:
            citing_work_str = ' '.join([citing_work_str, self.reference])
        return citing_work_str

    def index_with_respect_to_parent_object(self):
        return (*self.owner.original_texts.all(),).index(self)

    def ordinal_with_respect_to_parent_object(self):
        # if there are any sibling original texts then display
        # an ordinal a, b, c for this original text
        ordinal = ''
        if self.owner.original_texts.count() > 1:
            index = self.index_with_respect_to_parent_object()
            ordinal = chr(ord('a')+index)
        return ordinal

    # the ID to use in the concordance table
    @property
    def concordance_identifiers(self):
        # ordinal = ''
        # if self.owner.original_texts.count() > 1:
        #     index = self.index_with_respect_to_parent_object()
        #     ordinal = chr(ord('a')+index)
        ordinal = self.ordinal_with_respect_to_parent_object()
        return [
            '{}{}'.format(name, ordinal) for name in self.owner.get_all_names()
        ]

    def __str__(self):
        # one-indexed position of this wrt all the others (or pk as fallback)
        try:
            display_value = 1 + list(
                self.owner.original_texts.values_list('pk', flat=True)
            ).index(self.pk)
        except ValueError:
            display_value = self.pk
        return 'Original Text %d' % display_value


class Concordance(HistoryModelMixin, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.original_text.related_lock_object()

    original_text = models.ForeignKey('OriginalText', on_delete=models.CASCADE)

    source = models.CharField(max_length=128, blank=False)

    identifier = models.CharField(max_length=128, blank=False)

    class Meta:
        ordering = ('source', 'identifier')

    def __str__(self):
        return '%s:%s' % (self.source, self.identifier)


class Translation(HistoryModelMixin, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.original_text.related_lock_object()

    original_text = models.ForeignKey('OriginalText', on_delete=models.CASCADE)

    translator_name = models.CharField(max_length=128, blank=False)

    translated_text = models.TextField(blank=False)

    approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # if we are approved then all others are marked unapproved
        if self.approved:
            self.original_text.translation_set.exclude(
                pk=self.pk
            ).update(approved=False)
        super().save(*args, **kwargs)

    def __str__(self):
        # one-indexed position of this or pk
        try:
            display_value = 1 + list(
                self.original_text.translation_set.values_list('pk', flat=True)
            ).index(self.pk)
        except ValueError:
            display_value = self.pk
        return 'Translation %d' % display_value
