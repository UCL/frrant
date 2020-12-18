from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.urls import reverse

from rard.research.models.base import (AnonymousFragmentLink, FragmentLink,
                                       HistoricalBaseModel)
from rard.research.models.topic import Topic
from rard.utils.basemodel import OrderableModel


class TopicLink(models.Model):

    class Meta:
        ordering = ['order']

    topic = models.ForeignKey('Topic', null=False, on_delete=models.CASCADE)

    fragment = models.ForeignKey(
        'Fragment', null=False, on_delete=models.CASCADE)

    # with respect to topic
    order = models.IntegerField(default=None, null=True)


def handle_deleted_topic_link(sender, instance, **kwargs):
    instance.topic.reindex_fragment_links()


def handle_changed_topics(sender, instance, action, model, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove'):
        return

    from rard.research.models import Topic

    # find the Topic whose works have changed
    if isinstance(instance, Topic):
        instance.reindex_fragment_links()
    elif model == Topic:
        # they are adding a one or more antiquarians to a work
        # so iterate them all
        for topic in model.objects.filter(pk__in=pk_set):
            topic.reindex_fragment_links()


m2m_changed.connect(handle_changed_topics, sender=TopicLink)
post_delete.connect(handle_deleted_topic_link, sender=TopicLink)


class Fragment(HistoricalBaseModel):

    # fragments can also have topics
    topics = models.ManyToManyField('Topic', blank=True, through='TopicLink')

    original_texts = GenericRelation(
        'OriginalText', related_query_name='original_texts'
    )

    def _get_linked_works_and_books(self, definite):
        # a list of definite linked works and books
        all_links = self.antiquarian_fragmentlinks.filter(
            definite=definite,
            work__isnull=False,
        ).order_by('work', '-book').distinct()

        rtn = set()
        for link in all_links:
            if link.book:
                rtn.add(link.book)
            else:
                rtn.add(link.work)
        return rtn

    def possible_works_and_books(self):
        return self._get_linked_works_and_books(definite=False)

    def definite_works_and_books(self):
        return self._get_linked_works_and_books(definite=True)

    def definite_antiquarians(self):
        from rard.research.models import Antiquarian
        return Antiquarian.objects.filter(
            fragmentlinks__in=self.antiquarian_fragmentlinks.all(),
            fragmentlinks__definite=True,
            fragmentlinks__work__isnull=True,
        ).distinct()

    def possible_antiquarians(self):
        from rard.research.models import Antiquarian
        return Antiquarian.objects.filter(
            fragmentlinks__in=self.antiquarian_fragmentlinks.all(),
            fragmentlinks__definite=False,
            fragmentlinks__work__isnull=True,
        ).distinct()

    def get_absolute_url(self):
        return reverse('fragment:detail', kwargs={'pk': self.pk})

    def get_all_names(self):
        return [
            link.get_display_name()
            # for link in self.get_all_links().order_by(
            #     'antiquarian', 'order'
            # ).distinct()
            for link in self.get_all_links()
        ]

    def get_all_work_names(self):
        # all the names wrt works
        return [
            link.get_work_display_name()
            for link in self.get_all_links()
            # for link in self.get_all_links().order_by(
            #     'work', 'work_order'
            # ).distinct()
        ]

    def get_all_links(self):
        return FragmentLink.objects.filter(
            fragment=self
        ).order_by('antiquarian', 'order').distinct()


Fragment.init_text_object_fields()


class AnonymousTopicLink(models.Model):

    # need a different class for anonymous topics so they can
    # vary independently

    class Meta:
        ordering = ['order']

    topic = models.ForeignKey('Topic', null=False, on_delete=models.CASCADE)

    fragment = models.ForeignKey(
        'AnonymousFragment', null=False, on_delete=models.CASCADE)

    # with respect to topic
    order = models.IntegerField(default=None, null=True)


class AnonymousFragment(OrderableModel, HistoricalBaseModel):

    class Meta(HistoricalBaseModel.Meta):
        ordering = ['order']

    def related_queryset(self):
        return self.__class__.objects.all()

    # these can also have topics but ordering not yet clear
    topics = models.ManyToManyField(
        'Topic', blank=True, through='AnonymousTopicLink'
    )

    original_texts = GenericRelation(
        'OriginalText', related_query_name='original_texts'
    )

    def _get_linked_works_and_books(self, definite):
        # a list of definite linked works and books
        all_links = self.antiquarian_anonymousfragmentlinks.filter(
            definite=definite,
            work__isnull=False,
        ).order_by('work', '-book').distinct()

        rtn = set()
        for link in all_links:
            if link.book:
                rtn.add(link.book)
            else:
                rtn.add(link.work)
        return rtn

    def possible_works_and_books(self):
        return self._get_linked_works_and_books(definite=False)

    def definite_works_and_books(self):
        return self._get_linked_works_and_books(definite=True)

    def definite_antiquarians(self):
        from rard.research.models import Antiquarian
        all_links = self.antiquarian_anonymousfragmentlinks.all()
        return Antiquarian.objects.filter(
            anonymousfragmentlinks__in=all_links,
            anonymousfragmentlinks__definite=True,
            anonymousfragmentlinks__work__isnull=True,
        ).distinct()

    def possible_antiquarians(self):
        from rard.research.models import Antiquarian
        all_links = self.antiquarian_anonymousfragmentlinks.all()
        return Antiquarian.objects.filter(
            anonymousfragmentlinks__in=all_links,
            anonymousfragmentlinks__definite=False,
            anonymousfragmentlinks__work__isnull=True,
        ).distinct()

    def get_absolute_url(self):
        return reverse('anonymous_fragment:detail', kwargs={'pk': self.pk})

    def get_all_names(self):
        return [
            link.get_display_name()
            for link in self.get_all_links()
        ]

    def get_all_work_names(self):
        # all the names wrt works
        return [
            link.get_work_display_name()
            for link in self.get_all_links()
        ]

    def get_all_links(self):
        return AnonymousFragmentLink.objects.filter(
            fragment=self
        ).order_by('antiquarian', 'order').distinct()

    def get_display_name(self):
        return 'Anonymous F%s' % (self.order + 1)

    def save(self, *args, **kwargs):
        if self.order is None:
            self.order = self.__class__.objects.count()
        super().save(*args, **kwargs)

    @classmethod
    def reorder(cls):
        with transaction.atomic():
            for count, item in enumerate(cls.objects.all()):
                if item.order != count:
                    item.order = count
                    item.save()


AnonymousFragment.init_text_object_fields()


# handle changes in topic order and re-order anonymous fragments

def reindex_anonymous_fragments():
    # where there has been a change, ensure the
    # ordering of fragments is correct (zero-indexed)

    # single db update
    with transaction.atomic():

        anon_fragments = AnonymousFragment.objects.order_by(
            'topics__order', 'order'
        )
        # because we are ordering on an m2m field value we may have
        # duplicates in there. We want to remove these dupes but keep
        # the ordering of the list. Fast way is via a set of dict keys
        # which preserve ordering
        # NB list(set(items)) does not preserve ordering

        ordered = list(dict.fromkeys(list(anon_fragments)))
        for count, anon in enumerate(ordered):
            anon.order = count
            anon.save()


def handle_changed_anon_topics(sender, instance, **kwargs):
    reindex_anonymous_fragments()


def handle_changed_anon_topic_links(
        sender, instance, action, model, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove'):
        return

    reindex_anonymous_fragments()


m2m_changed.connect(handle_changed_anon_topic_links, sender=AnonymousTopicLink)
post_delete.connect(handle_changed_anon_topics, sender=AnonymousTopicLink)
post_save.connect(handle_changed_anon_topics, sender=Topic)
