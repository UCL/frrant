from unicodedata import name
import pytest
from unittest import skip
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
        fragment = AnonymousFragment.objects.create(**data)
        self.assertEqual(str(fragment), "Anonymous F1")

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
        fragment = AnonymousFragment.objects.create(name="name")
        citing_work = CitingWork.objects.create(title="title")
        data = {
            "content": "content",
            "citing_work": citing_work,
        }
        # it is unlinked so we show general
        OriginalText.objects.create(**data, owner=fragment)
        self.assertEqual(fragment.get_display_name(), "Anonymous F1")

    def test_get_display_name_no_original_text(self):
        fragment = Fragment.objects.create(name="name")
        self.assertEqual(fragment.get_display_name(), str(fragment))


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
        associated with that topic; e.g. if there are 10 AnonymousTopicLinks
        associated with the topic "Monarchy", a new AnonymousTopicLink
        associated with "Monarchy" should have order = 10."""
        self.anon2.topics.add(self.t1)
        new_link = AnonymousTopicLink.objects.filter(
            topic=self.t1, fragment=self.anon2
        ).first()
        # new_link.save()
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

        t2qs = AnonymousTopicLink.objects.filter(topic=self.t2)
        new_link3 = AnonymousTopicLink.objects.filter(
            topic=self.t2, fragment=self.anon2
        ).first()
        # if the index of anon2 is 1, remove anon1 and check index of anon2
        if (*t2qs,).index(new_link3) == 1:
            self.anon1.topics.remove(self.t2)
            t2qs = AnonymousTopicLink.objects.filter(topic=self.t2)
            new_link3_index = (*t2qs,).index(new_link3)
            self.assertEqual(new_link3_index, 0)
