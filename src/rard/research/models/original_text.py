from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.safestring import mark_safe
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.research.models.reference import Reference
from rard.utils.basemodel import BaseModel, DynamicTextField
from rard.utils.text_processors import make_plain_text


class OriginalText(HistoryModelMixin, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.owner

    class Meta:
        ordering = ("citing_work", "reference_order")

    @property
    def reference(self):
        references = Reference.objects.filter(original_text=self)
        if references:
            # only return the number values as the editor isn't critical
            return references.first().reference_position
        else:
            return ""

    @property
    def reference_list(self):
        """Returns a list of references with editor and ref position for each
        unless there's only one, in which case only the ref position is shown"""
        references = Reference.objects.filter(original_text=self)
        if references.count() > 1:
            return [
                f"{reference.editor} {reference.reference_position} |"
                for reference in references
            ]
        else:
            return [references.first().reference_position]

    # The value to be used in 'ordering by reference'
    # In some cases it will be a dot-separated list of numbers that also need
    # to be used for ordering, like 1.3.24.
    reference_order = models.CharField(
        blank=False, null=True, default=None, max_length=100
    )

    # original text can belong to either a fragment or a testimonium
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey()

    citing_work = models.ForeignKey("CitingWork", on_delete=models.CASCADE)

    content = DynamicTextField(blank=False)

    # Also store copy without html or punctuation for search purposes
    plain_content = models.TextField(blank=False, default="")

    # to be nuked eventually. not required now but hidden from view
    # to preserve previous values in case our data migration is insufficient
    apparatus_criticus = DynamicTextField(default="", blank=True)

    apparatus_criticus_items = GenericRelation(
        "ApparatusCriticusItem", related_query_name="original_text"
    )

    apparatus_criticus_blank = models.BooleanField(
        "no apparatus criticus exists", blank=False, null=False, default=False
    )

    def save(self, *args, **kwargs):
        """Save html free copy of text fields. We introduce a space
        between closing and opening tags so words at the beginning/end
        of list items don't get merged (and other things like that)"""
        if self.content:
            self.plain_content = make_plain_text(self.content)
        super(OriginalText, self).save(*args, **kwargs)

    def apparatus_criticus_lines(self):
        # use this rather than the above as that doesn't automatically
        # sort the results :/
        return self.apparatus_criticus_items.all().order_by("order")

    def citing_work_reference_display(self):
        citing_work_str = str(self.citing_work)
        if self.reference:
            citing_work_str = " ".join([citing_work_str, self.reference])
        return citing_work_str

    def index_with_respect_to_parent_object(self):
        return (*self.owner.original_texts.all(),).index(self)

    def ordinal_with_respect_to_parent_object(self):
        # if there are any sibling original texts then display
        # an ordinal a, b, c for this original text
        ordinal = ""
        if self.owner.original_texts.count() > 1:
            index = self.index_with_respect_to_parent_object()
            ordinal = chr(ord("a") + index)
        return ordinal

    def remove_reference_order_padding(self):
        # Remove leading 0s so we display the user-friendly version
        # e.g. 000001.000024.001230 will show as 1.24.1230
        return ".".join([i.lstrip("0") for i in self.reference_order.split(".")])

    # the ID to use in the concordance table
    @property
    def concordance_identifiers(self):
        # ordinal = ''
        # if self.owner.original_texts.count() > 1:
        #     index = self.index_with_respect_to_parent_object()
        #     ordinal = chr(ord('a')+index)
        ordinal = self.ordinal_with_respect_to_parent_object()
        return [
            mark_safe("{}{}".format(name, ordinal))
            for name in self.owner.get_all_names()
        ]

    def __str__(self):
        # one-indexed position of this wrt all the others (or pk as fallback)
        try:
            display_value = 1 + list(
                self.owner.original_texts.values_list("pk", flat=True)
            ).index(self.pk)
        except ValueError:
            display_value = self.pk
        return "Original Text %d" % display_value


class Concordance(HistoryModelMixin, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.original_text.related_lock_object()

    original_text = models.ForeignKey(
        "OriginalText", on_delete=models.CASCADE, related_name="concordances"
    )

    source = models.CharField(max_length=128, blank=False)

    identifier = models.CharField(max_length=128, blank=False)

    class Meta:
        ordering = ("source", "identifier")

    def __str__(self):
        return "%s: %s" % (self.source, self.identifier)


class Translation(HistoryModelMixin, BaseModel):

    history = HistoricalRecords()

    def related_lock_object(self):
        return self.original_text.related_lock_object()

    original_text = models.ForeignKey("OriginalText", on_delete=models.CASCADE)

    translator_name = models.CharField(max_length=128, blank=False)

    translated_text = models.TextField(blank=False)

    # plain copy for search purposes
    plain_translated_text = models.TextField(blank=False, default="")

    approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # if we are approved then all others are marked unapproved
        if self.approved:
            self.original_text.translation_set.exclude(pk=self.pk).update(
                approved=False
            )
        # make a plain copy
        if self.translated_text:
            self.plain_translated_text = make_plain_text(self.translated_text)
        super().save(*args, **kwargs)

    def __str__(self):
        # one-indexed position of this or pk
        try:
            display_value = 1 + list(
                self.original_text.translation_set.values_list("pk", flat=True)
            ).index(self.pk)
        except ValueError:
            display_value = self.pk
        return "Translation %d" % display_value
