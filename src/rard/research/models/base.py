from django.db import models
from django.db.models.signals import m2m_changed, post_delete
from django.db.utils import IntegrityError

from rard.research.models import Antiquarian
from rard.research.models.mixins import TextObjectFieldMixin
from rard.utils.basemodel import BaseModel, LockableModel


class LinkBaseModel(BaseModel):
    class Meta:
        ordering = ['order']
        abstract = True

    @property
    def linked(self):
        return getattr(self, self.linked_field)

    def related_queryset(self):
        return self.__class__.objects.filter(antiquarian=self.antiquarian)

    def prev(self):
        return self.related_queryset().filter(order__lt=self.order).last()

    def next(self):
        return self.related_queryset().filter(order__gt=self.order).first()

    def swap(self, replacement):
        self.order, replacement.order = replacement.order, self.order
        self.save()
        replacement.save()

    def up(self):
        previous = self.prev()
        if previous:
            self.swap(previous)

    def down(self):
        next_ = self.next()
        if next_:
            self.swap(next_)

    def save(self, *args, **kwargs):
        if not self.pk:
            # deduce the order of this fragment with respect to this work
            self.order = self.related_queryset().count()

        super().save(*args, **kwargs)

    def get_display_name(self):
        return '{} {}{}'.format(
            self.antiquarian or 'Anonymous',
            self.display_stub,
            self.display_order_one_indexed()
        )

    def display_order_one_indexed(self):
        return self.order + 1

    order = models.PositiveIntegerField(
        default=None, null=True, blank=True
    )
    antiquarian = models.ForeignKey(
        'Antiquarian',
        null=True,
        default=None,
        related_name='%(class)ss',
        on_delete=models.SET_NULL
    )

    definite = models.BooleanField(default=False)


class TestimoniumLink(LinkBaseModel):

    linked_field = 'testimonium'
    display_stub = 'T'

    testimonium = models.ForeignKey(
        'Testimonium',
        null=True,
        default=None,
        related_name='antiquarian_testimonium_links',
        on_delete=models.CASCADE
    )
    work = models.ForeignKey(
        'Work',
        null=True,
        default=None,
        related_name='antiquarian_work_testimonium_links',
        on_delete=models.CASCADE
    )
    # optional additional book information
    book = models.ForeignKey(
        'Book',
        null=True,
        default=None,
        related_name='antiquarian_book_testimonium_links',
        on_delete=models.CASCADE,
        blank=True
    )


class FragmentLink(LinkBaseModel):

    linked_field = 'fragment'
    display_stub = 'F'

    fragment = models.ForeignKey(
        'Fragment',
        null=True,
        default=None,
        related_name='antiquarian_fragment_links',
        on_delete=models.CASCADE
    )
    work = models.ForeignKey(
        'Work',
        null=True,
        default=None,
        related_name='antiquarian_work_fragment_links',
        on_delete=models.CASCADE
    )
    # optional additional book information
    book = models.ForeignKey(
        'Book',
        null=True,
        default=None,
        related_name='antiquarian_book_fragment_links',
        on_delete=models.CASCADE
    )


def check_order_info(sender, instance, action, model, pk_set, **kwargs):
    if action not in ['post_add', 'post_remove']:
        return

    from rard.research.models import Antiquarian, Fragment

    # what antiquarians does this event relate to?
    antiquarians = Antiquarian.objects.none()
    if isinstance(instance, Fragment):
        antiquarians = instance.linked_antiquarians.all()
    elif isinstance(instance, Antiquarian):
        antiquarians = Antiquarian.objects.filter(pk=instance.pk)

    for antiquarian in antiquarians:
        qs = sender.objects.filter(antiquarian=antiquarian)
        qs = qs.distinct()

        def check_existing_integrity(qs):
            # first check existing order is intact
            for count, link in enumerate(qs.all()):
                link.order = count
                link.save()

        if action == 'post_add':
            # patch any with no order info
            to_patch = qs.filter(order__isnull=True)
            okay = qs.filter(order__isnull=False)
            for count, intermed in enumerate(to_patch.all()):
                new_order = okay.count() + count
                # order at the end of the set
                intermed.order = new_order
                intermed.save()

        elif action == 'post_remove':
            check_existing_integrity(qs)


def reindex_order_info(sender, instance, **kwargs):
    qs = sender.objects.filter(antiquarian=instance.antiquarian)
    qs = qs.distinct()
    # set the order for the links
    for count, instance in enumerate(qs.all()):
        instance.order = count
        instance.save()

    for count, instance in enumerate(
            sender.objects.filter(antiquarian__isnull=True)):
        instance.order = count
        instance.save()


m2m_changed.connect(check_order_info, sender=FragmentLink)
post_delete.connect(reindex_order_info, sender=FragmentLink)
m2m_changed.connect(check_order_info, sender=TestimoniumLink)
post_delete.connect(reindex_order_info, sender=TestimoniumLink)


def works_changed(sender, instance, action, model, pk_set, **kwargs):
    if action not in ['post_add', 'post_remove', 'pre_clear', 'post_clear']:
        return

    if not isinstance(instance, Antiquarian):
        # we disallow adding antiquarians to works via the reverse accessor
        # as it is too problematic to unpick afterwards
        raise IntegrityError(
            "Link Antiquarian to Work via the works "
            "field of the Antiquarian model"
        )

    works = instance.works.all()

    if action == 'pre_clear':
        # have to love Django sometimes...
        # we are not passed the pk set of removed ids for the clear() method
        # unlike for remove, so we need towork it out
        # the values are only there for the pre_clear method, and only relevant
        # to the post_clear method. So deduce them in the pre_clear signal
        # then attach to the instance for the post_clear method to find
        pk_set = set(works.values_list('pk', flat=True))
        instance._pk_set = pk_set

    for model_class in [FragmentLink, TestimoniumLink]:
        # look at all linked works for this antiquarian
        qs = model_class.objects.filter(
            antiquarian=instance, work__isnull=False
        )

        if action in ('post_remove', 'post_clear'):
            if action == 'post_clear':
                pk_set = instance._pk_set

            # for all works that have no remaining antiquarians
            # we need to preserve fragment links to these works
            # but set the antiquarian to null

            from rard.research.models import Work
            orphaned_works = Work.objects.filter(
                pk__in=pk_set, antiquarian__isnull=True
            )

            preserve = qs.filter(work__in=orphaned_works)
            to_delete = qs.filter(work__pk__in=pk_set)

            stale = to_delete.exclude(pk__in=preserve)
            stale.delete()
            preserve.update(antiquarian=None)

        elif action == 'post_add':
            # look for fragment links to the added works and replicate them
            # for this antiquarian
            existing_links = model_class.objects.filter(
                work__pk__in=pk_set
            ).exclude(antiquarian=instance)

            for link in existing_links:
                # ensure we have one of each type
                data = {
                    'order': link.order,
                    'antiquarian': instance,
                    'work': link.work,
                    'definite': link.definite,
                    link.linked_field: getattr(link, link.linked_field)
                }
                model_class.objects.get_or_create(**data)

            # as we have definitely
            # got an anqiturian for this work, we can remove any stale
            # links to 'no antiquarian' here
            model_class.objects.filter(
                work__pk__in=pk_set, antiquarian__isnull=True
            ).delete()

        # now look for works that this antiquarian might have been added to,
        # that have links to fragments. Add link to this antiquarian

        # now re-index the remaining for this antiquarian
        for count, link in enumerate(
                model_class.objects.filter(antiquarian=instance)):
            link.order = count
            link.save()

        # and anonymous indexes
        for count, link in enumerate(
                model_class.objects.filter(antiquarian__isnull=True)):
            link.order = count
            link.save()


m2m_changed.connect(works_changed, sender=Antiquarian.works.through)


class HistoricalBaseModel(TextObjectFieldMixin, LockableModel, BaseModel):

    # abstract base class for shared properties of fragments and testimonia
    class Meta:
        abstract = True
        ordering = ['pk']

    name = models.CharField(max_length=128, blank=False)

    commentary = models.OneToOneField(
        'TextObjectField', on_delete=models.SET_NULL, null=True,
        related_name="commentary_for_%(class)s",
        blank=True,
    )

    images = models.ManyToManyField('Image', blank=True)

    def __str__(self):
        return self.get_display_name()

    def get_absolute_url(self):  # pragma: no cover
        class_name = self.__class__.__name__
        raise NotImplementedError(
            '%s must provide a get_absolute_url() method' % class_name
        )

    def get_display_name(self):
        # for displaying this fragment we use the name of the citing work(s)
        try:
            name = str(self.original_texts.first().citing_work)
            count = self.original_texts.count()
            if count > 1:
                name = '{} +{} more'.format(name, count-1)
            return name
        except AttributeError:
            return '{} {}'.format(self.__class__.__name__, self.pk)
