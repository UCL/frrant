from django.db import models, transaction
from django.db.models.signals import m2m_changed, post_delete, post_save

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
        return self.__class__.objects.filter(
            antiquarian=self.antiquarian).order_by('work__worklink__order')

    # def prev(self):
    #     return self.related_queryset().filter(order__lt=self.order).last()

    # def next(self):
    #     return self.related_queryset().filter(order__gt=self.order).first()

    # def swap(self, replacement):
    #     self.order, replacement.order = replacement.order, self.order
    #     self.save()
    #     replacement.save()

    # def up(self):
    #     previous = self.prev()
    #     if previous:
    #         self.swap(previous)

    # def down(self):
    #     next_ = self.next()
    #     if next_:
    #         self.swap(next_)

    def save(self, *args, **kwargs):
        if not self.pk:
            # deduce the order of this object with respect to its antiquarian
            self.order = self.related_queryset().count()

        super().save(*args, **kwargs)

    def get_display_name(self):
        return '{} {}{}'.format(
            self.antiquarian or 'Anonymous',
            self.get_display_stub(),
            self.display_order_one_indexed()
        )

    def get_display_stub(self):
        # offer a chance for subclasses to use logic to deduce this
        return self.display_stub

    def display_order_one_indexed(self):
        try:
            return self.order + 1
        except TypeError:
            return 'ERR'

    # the order wrt the antiquarian
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


class WorkLinkBaseModel(LinkBaseModel):
    class Meta(LinkBaseModel.Meta):
        abstract = True

    # the order wrt the work
    work_order = models.PositiveIntegerField(
        default=None, null=True, blank=True
     )

    def get_work_display_name(self):
        if not self.work:
            return ''

        return '{} {}{}'.format(
            self.work,
            self.get_display_stub(),
            self.display_work_order_one_indexed()
        )

    def get_work_display_name_full(self):
        # to also show the antiquarian link as well as the work link
        return '%s [= %s]' % (
            self.get_work_display_name(), self.get_display_name()
        )

    def display_work_order_one_indexed(self):
        try:
            return self.work_order + 1
        except TypeError:
            return 'ERR'

    def related_work_queryset(self):
        return self.__class__.objects.filter(
            work=self.work
        ).order_by('work_order')

    def prev_by_work(self):
        return self.related_work_queryset().filter(
            work_order__lt=self.work_order
        ).last()

    def next_by_work(self):
        return self.related_work_queryset().filter(
            work_order__gt=self.work_order
        ).first()

    def swap_by_work(self, replacement):
        self.work_order, replacement.work_order = \
            replacement.work_order, self.work_order
        self.save()
        replacement.save()
        if self.antiquarian:
            self.antiquarian.reindex_fragment_and_testimonium_links()

    def up_by_work(self):
        previous = self.prev_by_work()
        if previous:
            self.swap_by_work(previous)

    def down_by_work(self):
        next_ = self.next_by_work()
        if next_:
            self.swap_by_work(next_)

    work = models.ForeignKey(
        'Work',
        null=True,
        default=None,
        related_name='antiquarian_work_%(class)ss',
        on_delete=models.CASCADE
    )
    # optional additional book information
    book = models.ForeignKey(
        'Book',
        null=True,
        default=None,
        related_name='antiquarian_book_%(class)ss',
        on_delete=models.CASCADE,
        blank=True
    )

    def save(self, *args, **kwargs):
        # if not self.pk and self.work:
        #     # deduce the order of this object with respect to this work
        #     self.work_order = self.related_work_queryset().count()
        super().save(*args, **kwargs)


class TestimoniumLink(WorkLinkBaseModel):

    linked_field = 'testimonium'
    display_stub = 'T'

    testimonium = models.ForeignKey(
        'Testimonium',
        null=True,
        default=None,
        related_name='antiquarian_%(class)ss',
        on_delete=models.CASCADE
    )


class FragmentLink(WorkLinkBaseModel):

    linked_field = 'fragment'
    display_stub = 'F'

    fragment = models.ForeignKey(
        'Fragment',
        null=True,
        default=None,
        related_name='antiquarian_%(class)ss',
        on_delete=models.CASCADE
    )


class AnonymousFragmentLink(WorkLinkBaseModel):

    linked_field = 'fragment'
    display_stub = 'A'

    fragment = models.ForeignKey(
        'AnonymousFragment',
        null=True,
        default=None,
        related_name='antiquarian_%(class)ss',
        on_delete=models.CASCADE
    )


def check_order_info(sender, instance, action, model, pk_set, **kwargs):

    from rard.research.models import Antiquarian, Fragment, Testimonium

    if action not in ['post_add', 'post_remove']:
        return
    with transaction.atomic():
        # we might be handed the antiquarian or the fragment/testimonium
        # depending on which way round the change was made
        antiquarians = Antiquarian.objects.none()
        if isinstance(instance, (Fragment, Testimonium)):
            antiquarians = instance.linked_antiquarians.all()
        elif isinstance(instance, Antiquarian):
            antiquarians = Antiquarian.objects.filter(pk=instance.pk)

        for antiquarian in antiquarians.all():
            antiquarian.reindex_fragment_and_testimonium_links()

        Antiquarian.reindex_null_fragment_and_testimonium_links()


def handle_new_link(sender, instance, created, **kwargs):
    if created:
        reindex_order_info(sender, instance, **kwargs)


def reindex_order_info(sender, instance, **kwargs):

    # when we delete a fragmentlink we need to:
    # reindex all work_links for the work it pointed to
    with transaction.atomic():

        qs = instance.related_work_queryset()
        for count, item in enumerate(qs.all()):
            if item.work_order != count:
                item.work_order = count
                item.save()

        # request that the antiquarian involved reindex their fragment links
        if instance.antiquarian:
            instance.antiquarian.reindex_fragment_and_testimonium_links()

        # also check order of unattached links it
        # works for null antiquarian also
        Antiquarian.reindex_null_fragment_and_testimonium_links()


m2m_changed.connect(check_order_info, sender=FragmentLink)
post_save.connect(handle_new_link, sender=FragmentLink)
post_delete.connect(reindex_order_info, sender=FragmentLink)
m2m_changed.connect(check_order_info, sender=TestimoniumLink)
post_save.connect(handle_new_link, sender=TestimoniumLink)
post_delete.connect(reindex_order_info, sender=TestimoniumLink)


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
        return self.get_display_name_option_b()

    def _render_display_name(self, names):
        # render the output in the format required
        first_line = None
        if len(names) == 0:
            first_line = 'Unlinked {}'.format(self.pk)
        else:
            first_line = names[0]
            if len(names) > 1:
                also = ', '.join([name for name in names[1:]])
                if also:
                    first_line = '%s (also = %s)' % (first_line, also)
        return first_line

    def get_citing_display(self, for_citing_author=None):

        # if citing author passed as arg we need to put their original texts
        # first when displaying info
        if for_citing_author:
            this_author_texts = self.original_texts.filter(
                citing_work__author=for_citing_author
            )
            other = self.original_texts.exclude(pk__in=this_author_texts)
            all_texts = [x for x in this_author_texts] + [x for x in other]
        else:
            all_texts = [x for x in self.original_texts.all()]
        if len(all_texts) == 0:
            return '[]'

        first_text = all_texts[0]
        citing_work_str = str(first_text.citing_work)
        if len(all_texts) > 1:
            also = ', '.join([str(text.citing_work) for text in all_texts[1:]])
            if also:
                citing_work_str = '%s (also = %s)' % (citing_work_str, also)
        return citing_work_str

    def get_display_name_option_a(self):
        # show list of antiquarian links only
        links = self.get_all_links().order_by('antiquarian', 'order')
        names = [link.get_display_name() for link in links]
        return self._render_display_name(names)

    def get_link_names(self, show_certainty=True):
        links = self.get_all_links().order_by('work', 'antiquarian', 'order')
        names = []
        for link in links:
            if link.work:
                name = '%s [= %s]' % (
                    link.get_work_display_name(), link.get_display_name())
            else:
                name = '%s' % link.get_display_name()
            if show_certainty and not link.definite:
                name += ' (possible)'
            names.append(name)
        return names

    def get_display_name_option_b(self):
        # option b currently default
        names = self.get_link_names(show_certainty=False)
        return self._render_display_name(names)
