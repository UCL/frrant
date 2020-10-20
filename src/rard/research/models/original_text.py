from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext as _

from rard.utils.basemodel import BaseModel


class OriginalText(BaseModel):

    # original text can belong to either a fragment or a testimonium
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey()

    citing_work = models.ForeignKey('CitingWork', on_delete=models.CASCADE)

    # e.g. page 24
    reference = models.CharField(max_length=128, blank=True)

    content = models.TextField(blank=False)

    apparatus_criticus = models.TextField(default='', blank=True)

    # internal identifier for this original text (for eventual
    # use with concordance)
    # identifier = models.CharField(max_length=128, blank=False, default='')

    # the ID to use in the concordance table
    @property
    def concordance_identifier(self):
        return self.pk  # pragma: no cover


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


class CitingWork(BaseModel):

    # allow blank name as may be anonymous
    author = models.CharField(max_length=256, blank=True)

    title = models.CharField(max_length=256, blank=False)

    edition = models.CharField(max_length=128, blank=True)

    def __str__(self):
        tokens = [
            self.author if self.author else _('Anonymous'),
            self.title,
            self.edition
        ]
        return ', '.join([t for t in tokens if t])
