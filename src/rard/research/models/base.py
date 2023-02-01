from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.utils.safestring import mark_safe

from rard.research.models import Antiquarian
from rard.research.models.mixins import TextObjectFieldMixin
from rard.utils.basemodel import BaseModel, LockableModel
from rard.utils.decorators import disable_for_loaddata


class LinkBaseModel(BaseModel):
    class Meta:
        ordering = ["order"]
        abstract = True

    @property
    def linked(self):
        return getattr(self, self.linked_field)

    def related_queryset(self):
        return self.__class__.objects.filter(antiquarian=self.antiquarian).order_by(
            "-work__isnull", "work__worklink__order"
        )

    # keep these in case ever required again
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
        return "{} {}{}".format(
            self.antiquarian or "Anonymous",
            self.get_display_stub(),
            self.display_order_one_indexed(),
        )

    def get_display_stub(self):
        # offer a chance for subclasses to use logic to deduce this
        return self.display_stub

    def display_order_one_indexed(self):
        try:
            return self.order + 1
        except TypeError:
            return "ERR"

    # the order wrt the antiquarian
    order = models.PositiveIntegerField(default=None, null=True, blank=True)
    antiquarian = models.ForeignKey(
        "Antiquarian",
        null=True,
        default=None,
        related_name="%(class)ss",
        on_delete=models.SET_NULL,
    )

    definite = models.BooleanField(default=False)


class WorkLinkBaseModel(LinkBaseModel):
    class Meta(LinkBaseModel.Meta):
        abstract = True

    order_in_book = models.PositiveIntegerField(default=None, null=True, blank=True)
    # the order wrt the work
    work_order = models.PositiveIntegerField(default=None, null=True, blank=True)

    def get_work_display_name(self):
        if not self.work:
            return ""

        return "{} {}{}".format(
            self.work, self.get_display_stub(), self.display_work_order_one_indexed()
        )

    def get_work_display_name_full(self):
        # to also show the antiquarian link as well as the work link
        return "%s [= %s]" % (self.get_work_display_name(), self.get_display_name())

    def display_work_order_one_indexed(self):
        try:
            return self.work_order + 1
        except TypeError:
            return "ERR"

    def related_book_queryset(self):
        try:
            return self.__class__.objects.filter(book=self.book).order_by(
                "order_in_book"
            )
        except ObjectDoesNotExist:
            return self.__class__.objects.none()

    def prev_by_book(self):
        return (
            self.related_book_queryset()
            .filter(order_in_book__lt=self.order_in_book)
            .last()
        )

    def next_by_book(self):
        return (
            self.related_book_queryset()
            .filter(order_in_book__gt=self.order_in_book)
            .first()
        )

    def swap_by_book(self, replacement):
        self.order_in_book, replacement.order_in_book = (
            replacement.order_in_book,
            self.order_in_book,
        )
        self.save()
        replacement.save()
        if self.work:
            self.reindex_work_by_book()
        if self.antiquarian:
            self.antiquarian.reindex_fragment_and_testimonium_links()

    def move_to_by_book(self, pos):
        # move to a particular index in the set
        old_pos = self.order_in_book
        if pos == old_pos:
            return

        # if beyond the end, put it at the end (useful for UI)
        pos = min(pos, self.related_book_queryset().count())

        if pos < old_pos:
            to_reorder = (
                self.related_book_queryset()
                .exclude(pk=self.pk)
                .filter(order_in_book__gte=pos)
            )
            reindex_start_pos = pos + 1
        else:
            to_reorder = (
                self.related_book_queryset()
                .exclude(pk=self.pk)
                .filter(order_in_book__lte=pos)
            )
            reindex_start_pos = 0

        with transaction.atomic():
            for count, obj in enumerate(to_reorder):
                obj.order_in_book = count + reindex_start_pos
                obj.save()
            self.order_in_book = pos
            self.save()

        self.reindex_work_by_book()
        self.antiquarian.reindex_fragment_and_testimonium_links()
        Antiquarian.reindex_null_fragment_and_testimonium_links()

    def move_to_by_work(self, pos):
        # move to a particular index in the set
        old_pos = self.work_order
        if pos == old_pos:
            return

        # if beyond the end, put it at the end (useful for UI)
        pos = min(pos, self.related_work_queryset().count())

        if pos < old_pos:
            to_reorder = (
                self.related_work_queryset()
                .exclude(pk=self.pk)
                .filter(work_order__gte=pos)
            )
            reindex_start_pos = pos + 1
        else:
            to_reorder = (
                self.related_work_queryset()
                .exclude(pk=self.pk)
                .filter(work_order__lte=pos)
            )
            reindex_start_pos = 0

        with transaction.atomic():
            for count, obj in enumerate(to_reorder):
                obj.work_order = count + reindex_start_pos
                obj.save()
            self.work_order = pos
            self.save()
        self.antiquarian.reindex_fragment_and_testimonium_links()
        Antiquarian.reindex_null_fragment_and_testimonium_links()

    def up_by_book(self):
        previous = self.prev_by_book()
        if previous:
            self.swap_by_book(previous)

    def down_by_book(self):
        next_ = self.next_by_book()
        if next_:
            self.swap_by_book(next_)

    def reindex_work_by_book(self):
        from django.db import transaction

        with transaction.atomic():
            to_reorder = [
                self.__class__.objects.filter(work=self.work)
                .order_by("book__order", "order_in_book")
                .distinct()
            ]
            for count, link in enumerate(to_reorder):
                if link.order_in_book != count:
                    link.order_in_book = count
                    link.save()

    work = models.ForeignKey(
        "Work",
        null=True,
        default=None,
        related_name="antiquarian_work_%(class)ss",
        on_delete=models.CASCADE,
    )
    # optional additional book information
    book = models.ForeignKey(
        # this has book__order, not the same as order_in_book
        "Book",
        null=True,
        default=None,
        related_name="antiquarian_book_%(class)ss",
        on_delete=models.SET_NULL,
        blank=True,
    )

    def save(self, *args, **kwargs):
        # if not self.pk and self.work:
        #     # deduce the order of this object with respect to this work
        #     self.work_order = self.related_work_queryset().count()
        super().save(*args, **kwargs)


class TestimoniumLink(WorkLinkBaseModel):

    linked_field = "testimonium"
    display_stub = "T"

    testimonium = models.ForeignKey(
        "Testimonium",
        null=True,
        default=None,
        related_name="antiquarian_%(class)ss",
        on_delete=models.CASCADE,
    )


class FragmentLink(WorkLinkBaseModel):

    linked_field = "fragment"
    display_stub = "F"

    fragment = models.ForeignKey(
        "Fragment",
        null=True,
        default=None,
        related_name="antiquarian_%(class)ss",
        on_delete=models.CASCADE,
    )

    def get_concordance_identifiers(self):
        # only fragments have these, and we group them
        # on the concordance table according to the
        # name of the fragment link
        rtn = []
        for o in self.fragment.original_texts.all():
            rtn.extend([c for c in o.concordances.all()])
        return rtn


class AppositumFragmentLink(WorkLinkBaseModel):

    linked_field = "anonymous_fragment"
    display_stub = "A"

    # the anonymous fragment that is being linked:
    anonymous_fragment = models.ForeignKey(
        "AnonymousFragment",
        null=True,
        default=None,
        related_name="%(class)ss_from",
        on_delete=models.CASCADE,
    )

    # the optional fragment that the above anon fragment is being linked TO:
    linked_to = models.ForeignKey(
        "Fragment",
        null=True,
        default=None,
        related_name="%(class)ss_to",
        on_delete=models.CASCADE,
    )

    # whether links to works are to be stored just for this work/antiquarian
    # or whether they should be shared among other (and future) authors
    # of a work. NB not relevant where work is not specified.
    exclusive = models.BooleanField(default=False)

    # the association between apposita and fragments is done using another
    # relation as we might need those to be ordered wrt to the fragment

    # store the optional fragment link that generated this apposita link
    # and cascade on its deletion so we are auto-deleted
    link_object = models.ForeignKey(
        "FragmentLink", null=True, default=None, on_delete=models.CASCADE
    )

    def get_display_name(self):
        val = super().get_display_name()
        if self.exclusive:
            val = val + "*"
        if self.link_object:
            # if self.work is not None:
            #     sup = self.link_object.display_work_order_one_indexed()
            # else:
            sup = self.link_object.display_order_one_indexed()
            val = mark_safe("%s<sup>%s</sup>" % (val, sup))
        return val

    def get_work_display_name(self):
        val = super().get_work_display_name()
        if self.exclusive:
            val = val + "*"
        if self.link_object:
            # if self.work is not None:
            sup = self.link_object.display_work_order_one_indexed()
            # else:
            # sup = self.link_object.display_order_one_indexed()
            val = mark_safe("%s<sup>%s</sup>" % (val, sup))
        return val

    @classmethod
    def ensure_apposita_links(cls, instance):
        # instance is FragmentLink. When a linked fragment is
        # linked to something else then we need to reflect this
        # in the appositum links
        with transaction.atomic():
            for apposita in instance.fragment.apposita.all():
                AppositumFragmentLink.objects.get_or_create(
                    antiquarian=instance.antiquarian,
                    work=instance.work,
                    book=instance.book,
                    linked_to=instance.fragment,
                    anonymous_fragment=apposita,
                    link_object=instance,
                )


@disable_for_loaddata
def check_order_info(sender, instance, action, model, pk_set, **kwargs):

    from rard.research.models import Antiquarian, Fragment, Testimonium

    if action not in ["post_add", "post_remove"]:
        return

    with transaction.atomic():
        # we might be handed the antiquarian or the fragment/testimonium
        # depending on which way round the change was made
        antiquarians = Antiquarian.objects.none()
        if isinstance(instance, (Fragment, Testimonium)):
            antiquarians = instance.linked_antiquarians.all().distinct()
        elif isinstance(instance, Antiquarian):
            antiquarians = Antiquarian.objects.filter(pk=instance.pk)

        for antiquarian in antiquarians.all():
            antiquarian.reindex_fragment_and_testimonium_links()

        Antiquarian.reindex_null_fragment_and_testimonium_links()


@disable_for_loaddata
def handle_new_link(sender, instance, created, **kwargs):
    if created:
        if isinstance(instance, FragmentLink):
            AppositumFragmentLink.ensure_apposita_links(instance)
        reindex_order_info(sender, instance, **kwargs)


@disable_for_loaddata
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
m2m_changed.connect(check_order_info, sender=AppositumFragmentLink)
post_save.connect(handle_new_link, sender=AppositumFragmentLink)
post_delete.connect(reindex_order_info, sender=AppositumFragmentLink)
m2m_changed.connect(check_order_info, sender=TestimoniumLink)
post_save.connect(handle_new_link, sender=TestimoniumLink)
post_delete.connect(reindex_order_info, sender=TestimoniumLink)


class HistoricalBaseModel(TextObjectFieldMixin, LockableModel, BaseModel):

    # abstract base class for shared properties of fragments and testimonia
    class Meta:
        abstract = True
        ordering = ["pk"]

    # a placeholder 'entire collection' ID for this item. Current thinking
    # is that all fragments and anonymous fragments will be ordered by this
    # field, and testimonia separately. The rules for setting this ID will
    # be decided towards the project end and the entire collection will be
    # scanned and this ID set accordingly and then can be used as a
    # master index / order for the collection
    collection_id = models.PositiveIntegerField(default=None, null=True, blank=True)

    # Below is an example of how collection_id might be set by calling this
    # method at the end of the project. Beware when using order_by that if you
    # use a related field e.g. original text name, then you will get duplicate
    # fragments in your queryset where a fragment has multiple original texts
    # so you need care. Look at annotating the queryset for that:
    #
    # For example to order fragments by the first name of their original text
    # authors, we might do this:
    #
    # fragments = list(set(AnonymousFragment.objects.annotate(
    #     author_name=F('original_texts__citing_work__author__name')
    #     ).order_by('author_name')))
    #
    # using list(set(...)) removes duplicates from the collection which
    # have been ordered so our list is ordered by the name of the
    # author of the their original texts

    # However, below as an example we are using creation date of the record
    # which will not result in any duplicates as it is a value of the objects
    # themselves (rather than value(s) from potentially many related fields)

    @classmethod
    def reindex_collection(cls):
        from rard.research.models import AnonymousFragment, Fragment, Testimonium

        with transaction.atomic():
            for count, testimonium in enumerate(
                Testimonium.objects.order_by("created")
            ):
                testimonium.collection_id = count
                testimonium.save()

            qs1 = AnonymousFragment.objects.all()
            qs2 = Fragment.objects.all()
            # we cannot combine querysets directly with different models
            # but we can form a (large) list
            import operator
            from itertools import chain

            # sort them by created date in this example. Change this to
            # whichever shared key they have. Use annotate on the original
            # querysets where you need a related field value for both
            # e.g. original text name
            items = list(chain(qs1, qs2))
            items.sort(key=operator.attrgetter("created"))
            for count, item in enumerate(items):
                item.collection_id = count
                item.save()

    name = models.CharField(max_length=128, blank=False)

    commentary = models.OneToOneField(
        "TextObjectField",
        on_delete=models.SET_NULL,
        null=True,
        related_name="commentary_for_%(class)s",
        blank=True,
    )

    plain_commentary = models.TextField(blank=False, default="")

    images = models.ManyToManyField("Image", blank=True)

    def __str__(self):
        return self.get_display_name()

    def get_absolute_url(self):  # pragma: no cover
        class_name = self.__class__.__name__
        raise NotImplementedError(
            "%s must provide a get_absolute_url() method" % class_name
        )

    def get_display_name(self):
        return self.get_display_name_option_b()

    def _render_display_name(self, names, add_also=True):
        # render the output in the format required
        first_line = None
        if len(names) == 0:
            first_line = "Unlinked {}".format(self.pk)
        else:
            first_line = names[0]
            if add_also:
                if len(names) > 1:
                    also = ", ".join([name for name in names[1:]])
                    if also:
                        first_line = '%s <span class="also">' "(also = %s)</span>" % (
                            first_line,
                            also,
                        )
        return mark_safe(first_line)

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
            return "[]"

        first_text = all_texts[0]
        citing_work_str = first_text.citing_work_reference_display()
        if len(all_texts) > 1:
            also = ", ".join(
                [txt.citing_work_reference_display() for txt in all_texts[1:]]
            )
            if also:
                citing_work_str = "%s (also = %s)" % (citing_work_str, also)
        return citing_work_str

    def get_display_name_option_a(self):
        # show list of antiquarian links only
        links = self.get_all_links().order_by("antiquarian", "order")
        names = [link.get_display_name() for link in links]
        return self._render_display_name(names)

    def get_display_name_option_c(self):
        # remove (also = )
        names = self.get_link_names(show_certainty=False)
        return self._render_display_name(names, add_also=False)

    def get_link_names(self, show_certainty=True):
        links = self.get_all_links().order_by("work", "antiquarian", "order")
        names = []
        for link in links:
            if link.work:
                name = "%s [= %s]" % (
                    link.get_work_display_name(),
                    link.get_display_name(),
                )
            else:
                name = "%s" % link.get_display_name()
            if show_certainty and not link.definite:
                name += " (possible)"
            names.append(name)
        return names

    def get_display_name_option_b(self):
        # option b currently default
        names = self.get_link_names(show_certainty=False)
        return self._render_display_name(names)
