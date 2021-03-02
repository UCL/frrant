from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import (m2m_changed, post_delete, post_save,
                                      pre_delete)
from django.urls import reverse
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryViewMixin, TextObjectFieldMixin
from rard.utils.basemodel import (BaseModel, DatedModel, LockableModel,
                                  OrderableModel)


class WorkLink(OrderableModel, models.Model):

    class Meta:
        ordering = ['order']

    def related_queryset(self):
        return self.__class__.objects.filter(antiquarian=self.antiquarian)

    antiquarian = models.ForeignKey(
        'Antiquarian', null=False, on_delete=models.CASCADE
    )

    work = models.ForeignKey('Work', null=False, on_delete=models.CASCADE)

    # # with respect to antiquarian
    # order = models.IntegerField(default=None, null=True)


def handle_deleted_work_link(sender, instance, **kwargs):

    if instance.work and instance.work.antiquarian_set.count() == 0:
        work = instance.work
        # prevent multiple anon links
        instance.antiquarian.fragmentlinks.filter(
            work=work).filter(antiquarian=None).delete()
        instance.antiquarian.fragmentlinks.filter(
            work=work).update(antiquarian=None)
        instance.antiquarian.testimoniumlinks.filter(
            work=work).filter(antiquarian=None).delete()
        instance.antiquarian.testimoniumlinks.filter(
            work=work).update(antiquarian=None)
        # same for appositum
        instance.antiquarian.appositumfragmentlinks.filter(
            work=work).filter(antiquarian=None).delete()
        # null non-exclusive links
        instance.antiquarian.appositumfragmentlinks.filter(
            work=work, exclusive=False).update(antiquarian=None)
        # delete exclusive links
        instance.antiquarian.appositumfragmentlinks.filter(
            work=work, exclusive=True).delete()

    instance.antiquarian.reindex_work_links()
    instance.antiquarian.reindex_fragment_and_testimonium_links()


def handle_reordered_works(sender, instance, created, **kwargs):
    if not created:
        # Only handle modified links here.
        # If a new one created then this is handled in m2m_changed
        # which only works for add/remove links, not modified so we
        # need to handle modified here.
        instance.antiquarian.reindex_fragment_and_testimonium_links()


def handle_changed_works(sender, instance, action, model, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove'):
        return

    adding = action == 'post_add'

    from rard.research.models import Antiquarian, Work

    # find the antiquarian whose works have changed
    if isinstance(instance, Antiquarian):
        works = Work.objects.filter(pk__in=pk_set)

        instance.reindex_work_links()
        if adding:
            for work in works:
                instance.copy_links_for_work(work)
        instance.reindex_fragment_and_testimonium_links()

    elif model == Antiquarian:
        # they are adding a one or more antiquarians to a work
        # so iterate them all
        for antiquarian in model.objects.filter(pk__in=pk_set):
            antiquarian.reindex_work_links()
            if adding:
                antiquarian.copy_links_for_work(instance)
            antiquarian.reindex_fragment_and_testimonium_links()


m2m_changed.connect(handle_changed_works, sender=WorkLink)
post_delete.connect(handle_deleted_work_link, sender=WorkLink)
post_save.connect(handle_reordered_works, sender=WorkLink)


class Antiquarian(HistoryViewMixin, TextObjectFieldMixin, LockableModel,
                  DatedModel, BaseModel):

    history = HistoricalRecords(
        excluded_fields=[
        ]
    )

    def related_lock_object(self):
        return self

    class Meta:
        ordering = ['order_name', 're_code']

    name = models.CharField(max_length=128, blank=False)

    order_name = models.CharField(max_length=128, default='', blank=True)

    introduction = models.OneToOneField(
        'TextObjectField', on_delete=models.SET_NULL, null=True,
        related_name='introduction_for'
    )

    re_code = models.CharField(
        max_length=64, blank=False, unique=True, verbose_name='RE Number'
    )

    works = models.ManyToManyField(
        'Work', blank=True,
        through='WorkLink'
    )

    fragments = models.ManyToManyField(
        'Fragment', related_name='linked_%(class)ss', blank=True,
        through='FragmentLink'
    )

    testimonia = models.ManyToManyField(
        'Testimonium', related_name='linked_%(class)ss', blank=True,
        through='TestimoniumLink'
    )

    bibliography_items = GenericRelation(
        'BibliographyItem', related_query_name='bibliography_items'
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('antiquarian:detail', kwargs={'pk': self.pk})

    def ordered_fragments(self):
        return self.fragments.distinct()

    def save(self, *args, **kwargs):
        if not self.order_name:
            self.order_name = self.name
        super().save(*args, **kwargs)

    @property
    def ordered_works(self):
        # ordered
        from rard.research.models import Work
        return Work.objects.filter(
            worklink__antiquarian=self).order_by('worklink__order')

    def reindex_work_links(self):
        # where there has been a change, ensure the
        # ordering of works is correct (zero-indexed)
        from django.db import transaction

        # single db update
        with transaction.atomic():
            links = WorkLink.objects.filter(
                antiquarian=self).order_by(
                    models.F(('order')).asc(nulls_first=False))
            for count, link in enumerate(links):
                if link.order != count:
                    link.order = count
                    link.save()

    @classmethod
    def reindex_null_fragment_and_testimonium_links(cls):
        # any links that have no antiquarian attached, reorder them
        from rard.research.models.base import (AppositumFragmentLink,
                                               FragmentLink, TestimoniumLink)
        to_reorder = [
            FragmentLink.objects.filter(
                antiquarian=None).order_by(
                    'work__worklink__order', 'work_order').distinct(),
            TestimoniumLink.objects.filter(
                antiquarian=None).order_by(
                    'work__worklink__order', 'work_order').distinct(),
            AppositumFragmentLink.objects.filter(
                antiquarian=None).order_by(
                    'work__worklink__order', 'work_order').distinct(),
        ]

        for qs in to_reorder:
            for count, link in enumerate(qs):
                if link.order != count:
                    link.order = count
                    link.save()

    def copy_links_for_work(self, work):
        # copy links from one work to another

        from django.db import transaction

        from rard.research.models.base import (AppositumFragmentLink,
                                               FragmentLink, TestimoniumLink)

        with transaction.atomic():

            to_ensure = [
                FragmentLink.objects.filter(
                    work=work).exclude(antiquarian=self),
                TestimoniumLink.objects.filter(
                    work=work).exclude(antiquarian=self),
                AppositumFragmentLink.objects.filter(
                    work=work, exclusive=False).exclude(antiquarian=self),
            ]
            for qs in to_ensure:
                for link in qs:
                    data = {
                        'order': link.order,
                        'antiquarian': self,
                        'work': link.work,
                        'book': link.book,
                        'definite': link.definite,
                        link.linked_field: getattr(link, link.linked_field)
                    }
                    link.__class__.objects.get_or_create(**data)

            # remove unlinked
            stale = [
                FragmentLink.objects.filter(
                    work=work, antiquarian=None),
                TestimoniumLink.objects.filter(
                    work=work, antiquarian=None),
                AppositumFragmentLink.objects.filter(
                    work=work, antiquarian=None),
            ]

            for qs in stale:
                qs.delete()

    def reindex_fragment_and_testimonium_links(self):

        # when the order of works changes wrt to this antiquarian we need to
        # reflect these changes in all of our linked fragments and testimonia

        from django.db import transaction

        with transaction.atomic():

            # for any works that were linked to this antiquarian but still have
            # other authors, we need to delete our links to those works
            deleteable = [
                self.fragmentlinks.filter(
                    work__isnull=False, work__antiquarian__isnull=False
                ).exclude(work__in=self.works.all()),
                self.testimoniumlinks.filter(
                    work__isnull=False, work__antiquarian__isnull=False
                ).exclude(work__in=self.works.all()),
                self.appositumfragmentlinks.filter(
                    work__isnull=False, exclusive=False,
                    work__antiquarian__isnull=False
                ).exclude(work__in=self.works.all()),
            ]

            # delete any exclusive links here
            deleteable += [
                self.appositumfragmentlinks.filter(
                    work__isnull=False, exclusive=True).exclude(
                        work__in=self.works.all()
                    ),
            ]
            for qs in deleteable:
                # these are stale links and should be removed
                qs.delete()

            # works that have no antiquarians left now that our link
            # has been removed can have their links' antiquarian set to null
            # so that the fragment etc remains linked to the antiquarian
            # However if they still have an author we need to delete
            # the link in the step after

            nullable = [
                self.fragmentlinks.filter(
                    work__isnull=False, work__antiquarian__isnull=True
                ).exclude(work__in=self.works.all()),
                self.testimoniumlinks.filter(
                    work__isnull=False, work__antiquarian__isnull=True
                ).exclude(work__in=self.works.all()),
                self.appositumfragmentlinks.filter(
                    work__isnull=False, exclusive=False,
                    work__antiquarian__isnull=True
                ).exclude(work__in=self.works.all()),
            ]
            for qs in nullable:
                # set the antiquarian to None for these links
                # i.e. we preserve links from objects to the work
                # even if there is now no antiquarian for that work
                qs.update(antiquarian=None)

            to_reorder = [
                self.fragmentlinks.all().order_by(
                    'work__worklink__order', 'work_order').distinct(),
                self.testimoniumlinks.all().order_by(
                    'work__worklink__order', 'work_order').distinct(),
                self.appositumfragmentlinks.all().order_by(
                    'work__worklink__order', 'work_order').distinct(),
            ]

            for qs in to_reorder:
                for count, link in enumerate(qs):
                    if link.order != count:
                        link.order = count
                        link.save()

            self.reindex_null_fragment_and_testimonium_links()


def remove_stale_antiquarian_links(sender, instance, **kwargs):
    # when deleting an antiquarian,
    # any fragment or testimonium links to the antiquarian
    # (and not via a work) should be deleted here
    from rard.research.models.base import (AppositumFragmentLink, FragmentLink,
                                           TestimoniumLink)

    qs = FragmentLink.objects.filter(
        antiquarian=instance, work__isnull=True
    )
    qs.delete()

    qs = TestimoniumLink.objects.filter(
        antiquarian=instance, work__isnull=True
    )
    qs.delete()

    qs = AppositumFragmentLink.objects.filter(
        antiquarian=instance, work__isnull=True
    )
    # delete any exclusive links
    qs = AppositumFragmentLink.objects.filter(
        antiquarian=instance, exclusive=True
    )
    qs.delete()


pre_delete.connect(remove_stale_antiquarian_links, sender=Antiquarian)


Antiquarian.init_text_object_fields()
