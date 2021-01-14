from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rard.utils.basemodel import BaseModel


class OriginalText(BaseModel):

    class Meta:
        ordering = ('citing_work', 'reference')

    # original text can belong to either a fragment or a testimonium
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey()

    citing_work = models.ForeignKey('CitingWork', on_delete=models.CASCADE)

    # e.g. page 24
    reference = models.CharField(max_length=128, blank=True)

    content = models.TextField(blank=False)

    apparatus_criticus = models.TextField(default='', blank=True)

    def citing_work_reference_display(self):
        citing_work_str = str(self.citing_work)
        if self.reference:
            citing_work_str = ' '.join([citing_work_str, self.reference])
        return citing_work_str

    # the ID to use in the concordance table
    @property
    def concordance_identifiers(self):
        ordinal = ''
        if self.owner.original_texts.count() > 1:
            index = (*self.owner.original_texts.all(),).index(self)
            ordinal = chr(ord('a')+index)
        return [
            '{}{}'.format(name, ordinal) for name in self.owner.get_all_names()
        ]


class Concordance(BaseModel):

    original_text = models.ForeignKey('OriginalText', on_delete=models.CASCADE)

    source = models.CharField(max_length=128, blank=False)

    identifier = models.CharField(max_length=128, blank=False)

    class Meta:
        ordering = ('source', 'identifier')


class Translation(BaseModel):

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
