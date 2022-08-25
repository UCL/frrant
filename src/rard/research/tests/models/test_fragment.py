import pytest
from django.test import TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    AnonymousTopicLink,
    Antiquarian,
    CitingWork,
    Fragment,
    OriginalText,
    TextObjectField,
    Topic,
)
from rard.research.models.base import AppositumFragmentLink

pytestmark = pytest.mark.django_db


class TestFragment(TestCase):
    def test_creation(self):
        # can create with a name only
        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(fragment.name, data["name"])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(Fragment._meta.get_field("name").blank)

        # not required on forms
        self.assertTrue(Fragment._meta.get_field("images").blank)
        self.assertTrue(Fragment._meta.get_field("topics").blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(str(fragment), "Unlinked {}".format(fragment.pk))

    def test_initial_images(self):
        fragment = Fragment.objects.create(name="name")
        self.assertEqual(fragment.images.count(), 0)

    def test_initial_topics(self):
        fragment = Fragment.objects.create(name="name")
        self.assertEqual(fragment.topics.count(), 0)

    def test_commentary_created(self):
        fragment = Fragment.objects.create(name="name")
        self.assertIsNotNone(fragment.commentary.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=fragment.commentary.pk), fragment.commentary
        )

    def test_commentary_deleted(self):
        fragment = Fragment.objects.create(name="name")
        commentary_pk = fragment.commentary.pk
        fragment.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=commentary_pk)

    def test_get_absolute_url(self):
        fragment = Fragment.objects.create(name="name")
        self.assertEqual(
            fragment.get_absolute_url(),
            reverse("fragment:detail", kwargs={"pk": fragment.pk}),
        )

    def test_get_display_name(self):
        # we need to show the name of the first citing work of original texts
        fragment = Fragment.objects.create(name="name")
        citing_work = CitingWork.objects.create(title="title")
        data = {
            "content": "content",
            "citing_work": citing_work,
        }
        # it is unlinked so we show unlinked indicator
        OriginalText.objects.create(**data, owner=fragment)
        self.assertEqual(fragment.get_display_name(), "Unlinked %d" % fragment.pk)

    def test_get_display_name_no_original_text(self):
        fragment = Fragment.objects.create(name="name")
        self.assertEqual(fragment.get_display_name(), str(fragment))


class TestAnonymousFragment(TestCase):
    def test_creation(self):
        # can create with a name only
        data = {
            "name": "name",
        }
        fragment = AnonymousFragment.objects.create(**data)
        self.assertEqual(fragment.name, data["name"])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(AnonymousFragment._meta.get_field("name").blank)

        # not required on forms
        self.assertTrue(AnonymousFragment._meta.get_field("images").blank)
        self.assertTrue(AnonymousFragment._meta.get_field("topics").blank)
        self.assertTrue(AnonymousFragment._meta.get_field("fragments").blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            "name": "name",
        }
        initial_count = AnonymousFragment.objects.count()
        fragment = AnonymousFragment.objects.create(**data)
        self.assertEqual(fragment.order, initial_count)
        self.assertEqual(str(fragment), f"Anonymous F{initial_count + 1}")

    def test_initial_images(self):
        fragment = AnonymousFragment.objects.create(name="name")
        self.assertEqual(fragment.images.count(), 0)

    def test_initial_topics(self):
        fragment = AnonymousFragment.objects.create(name="name")
        self.assertEqual(fragment.topics.count(), 0)

    def test_commentary_created(self):
        fragment = AnonymousFragment.objects.create(name="name")
        self.assertIsNotNone(fragment.commentary.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=fragment.commentary.pk), fragment.commentary
        )

    def test_commentary_deleted(self):
        fragment = AnonymousFragment.objects.create(name="name")
        commentary_pk = fragment.commentary.pk
        fragment.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=commentary_pk)

    def test_get_absolute_url(self):
        fragment = AnonymousFragment.objects.create(name="name")
        self.assertEqual(
            fragment.get_absolute_url(),
            reverse("anonymous_fragment:detail", kwargs={"pk": fragment.pk}),
        )

    def test_get_display_name(self):
        # we need to show the name of the first citing work of original texts
        initial_count = AnonymousFragment.objects.count()
        fragment = AnonymousFragment.objects.create(name="name")
        citing_work = CitingWork.objects.create(title="title")
        data = {
            "content": "content",
            "citing_work": citing_work,
        }
        # it is unlinked so we show general
        OriginalText.objects.create(**data, owner=fragment)
        self.assertEqual(fragment.get_display_name(), f"Anonymous F{initial_count + 1}")

    def test_get_display_name_no_original_text(self):
        fragment = Fragment.objects.create(name="name")
        self.assertEqual(fragment.get_display_name(), str(fragment))

    @classmethod
    def setUpTestData(cls):

        cls.anon1 = AnonymousFragment.objects.create(name="anon1")
        cls.anon2 = AnonymousFragment.objects.create(name="anon2")
        cls.anon3 = AnonymousFragment.objects.create(name="anon3")

        cls.t1 = Topic.objects.create(name="Monarchy", order=0)
        cls.t2 = Topic.objects.create(name="Law", order=1)

        cls.f1 = Fragment.objects.create(name="frag1")
        AppositumFragmentLink.objects.create(
            anonymous_fragment=cls.anon3, linked_to=cls.f1
        )

        cls.anon1.topics.add(cls.t1)
        cls.anon2.topics.add(cls.t1)
        cls.anon3.topics.add(cls.t1)

        cls.anon2.topics.add(cls.t2)
        cls.anon1.topics.add(cls.t2)

    def test_reindex_anonymous_fragments_order_by_topic(self):
        """When reindexing anonymous fragments, topic order should take precedence
        over order within topic."""
        self.assertLess(self.anon1.order, self.anon2.order)
        self.assertEqual(self.t1.order, 0)
        self.t1.swap(self.t2)
        self.anon1.refresh_from_db()
        self.anon2.refresh_from_db()

        self.assertLess(self.anon2.order, self.anon1.order)

    def test_reindex_anonymous_fragments_order_by_topic_link_order(self):
        """When reindexing anonymous fragments, their order with respect to topics
        should be taken into account. Where two fragments both belong to the same two
        topics and their order relative to each other is different within those topics,
        their order with respect to the topic with lower order should take precedence.
        """

        atl_1 = AnonymousTopicLink.objects.filter(
            topic=self.t1, fragment=self.anon1
        ).first()
        atl_2 = AnonymousTopicLink.objects.filter(
            topic=self.t1, fragment=self.anon2
        ).first()
        atl_4 = AnonymousTopicLink.objects.filter(
            topic=self.t2, fragment=self.anon1
        ).first()
        atl_5 = AnonymousTopicLink.objects.filter(
            topic=self.t2, fragment=self.anon2
        ).first()

        """if the orders of atl_1 and atl_2 are swapped, anon2 should now have a
        lower order than anon1"""
        self.assertLess(atl_1.order, atl_2.order)
        self.assertLess(self.anon1.order, self.anon2.order)
        atl_1.swap(atl_2)
        self.anon1.refresh_from_db()
        self.anon2.refresh_from_db()
        self.assertLess(self.anon2.order, self.anon1.order)

        """if atl_4 and atl_5 are then swapped, anon2 should still have a lower
        order than anon1"""
        atl_4.swap(atl_5)
        self.anon1.refresh_from_db()
        self.anon2.refresh_from_db()
        self.assertLess(self.anon2.order, self.anon1.order)


class TestAnonymousTopicLink(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.anon1 = AnonymousFragment.objects.create(name="anon1")
        cls.anon2 = AnonymousFragment.objects.create(name="anon2")
        cls.anon3 = AnonymousFragment.objects.create(name="anon3")
        cls.t1 = Topic.objects.create(name="topic1")
        cls.t2 = Topic.objects.create(name="topic2")
        cls.anon1.topics.add(cls.t1)

        cls.a1 = Antiquarian.objects.create(name="a1")
        AppositumFragmentLink.objects.create(
            anonymous_fragment=cls.anon3, antiquarian=cls.a1
        )

    def test_new_link_order_is_last_if_not_apposita(self):
        """When a new AnonymousTopicLink is saved, it should be given
        an order value equal to the number of pre-existing links
        associated with that topic plus 1; e.g. if there are 10 AnonymousTopicLinks
        associated with the topic "Monarchy", a new AnonymousTopicLink
        associated with "Monarchy" should have order = 11."""
        self.anon2.topics.add(self.t1)
        new_link = AnonymousTopicLink.objects.filter(
            topic=self.t1, fragment=self.anon2
        ).first()
        # new_link should have order 2 because the topic already
        # contained one anonymous fragment
        self.assertEqual(new_link.order, 2)

    def test_new_link_order_is_zero_if_apposita(self):
        """When a new AnonymousTopicLink is saved, and the fragment is an apposita,
        it should be given an order of zero."""
        self.anon3.topics.add(self.t1)
        self.anon3.save()
        new_link2 = AnonymousTopicLink.objects.filter(
            topic=self.t1, fragment=self.anon3
        ).first()
        self.assertEqual(new_link2.order, 0)

    def test_links_reindexed_when_link_removed(self):
        """When an AnonymousTopicLink is deleted, anonymous topic links within
        the affected topic should be reindexed"""
        self.anon1.topics.add(self.t2)
        self.anon2.topics.add(self.t2)

        anon1_link = AnonymousTopicLink.objects.filter(
            topic=self.t2, fragment=self.anon1
        ).first()
        anon2_link = AnonymousTopicLink.objects.filter(
            topic=self.t2, fragment=self.anon2
        ).first()
        self.assertEqual([anon1_link.order, anon2_link.order], [1, 2])
        self.anon1.topics.remove(self.t2)
        anon2_link.refresh_from_db()
        self.assertEqual(anon2_link.order, 1)

    def test_link_order_change_updates_anon_fragment_order(self):
        """when AnonymousTopicLinks are reordered within a topic,
        anonymous fragments should be reindexed to take this into
        account; e.g. assert AnonymousFragment.reindex_anonymous_fragments
        is called when link order changes"""

        self.anon2.topics.add(self.t1)
        self.assertEqual([self.anon1.order, self.anon2.order], [0, 1])

        atl = AnonymousTopicLink.objects.filter(
            topic=self.t1, fragment=self.anon2
        ).first()
        atl.up()
        self.assertEqual(atl.order, 1)
        self.anon2.refresh_from_db()
        self.anon1.refresh_from_db()

        self.assertEqual([self.anon1.order, self.anon2.order], [1, 0])

    def test_apposita_not_in_related_queryset(self):
        # check anon3 not in a qs
        self.t3 = Topic.objects.create(name="topic3")
        self.anon1.topics.add(self.t3)
        self.anon2.topics.add(self.t3)
        self.anon3.topics.add(self.t3)

        anon1_topiclink = AnonymousTopicLink.objects.filter(
            topic=self.t3, fragment=self.anon1
        ).first()

        anon3_topiclink = AnonymousTopicLink.objects.filter(
            topic=self.t3, fragment=self.anon3
        ).first()

        anon1qs = anon1_topiclink.related_queryset()

        self.assertIn(anon1_topiclink, anon1qs)
        self.assertNotIn(anon3_topiclink, anon1qs)
