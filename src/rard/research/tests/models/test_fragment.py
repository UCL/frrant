
import pytest
from django.test import TestCase
from django.urls import reverse

from rard.research.models import (AnonymousFragment, CitingWork, Fragment,
                                  OriginalText)

pytestmark = pytest.mark.django_db


class TestFragment(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'name',
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(fragment.name, data['name'])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(Fragment._meta.get_field('name').blank)

        # not required on forms
        self.assertTrue(Fragment._meta.get_field('images').blank)
        self.assertTrue(Fragment._meta.get_field('topics').blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'name',
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(str(fragment), 'Unlinked {}'.format(fragment.pk))

    def test_initial_images(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.images.count(), 0)

    def test_initial_topics(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.topics.count(), 0)

    def test_get_absolute_url(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(
            fragment.get_absolute_url(),
            reverse('fragment:detail', kwargs={'pk': fragment.pk})
        )

    def test_get_display_name(self):
        # we need to show the name of the first citing work of original texts
        fragment = Fragment.objects.create(name='name')
        citing_work = CitingWork.objects.create(title='title')
        data = {
            'content': 'content',
            'citing_work': citing_work,
        }
        # it is unlinked so we show unlinked indicator
        OriginalText.objects.create(**data, owner=fragment)
        self.assertEqual(
            fragment.get_display_name(),
            'Unlinked %d' % fragment.pk
        )

    def test_get_display_name_no_original_text(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.get_display_name(), str(fragment))


class TestAnonymousFragment(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'name',
        }
        fragment = AnonymousFragment.objects.create(**data)
        self.assertEqual(fragment.name, data['name'])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(AnonymousFragment._meta.get_field('name').blank)

        # not required on forms
        self.assertTrue(AnonymousFragment._meta.get_field('images').blank)
        self.assertTrue(AnonymousFragment._meta.get_field('topics').blank)
        self.assertTrue(AnonymousFragment._meta.get_field('fragments').blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'name',
        }
        fragment = AnonymousFragment.objects.create(**data)
        self.assertEqual(str(fragment), 'Anonymous F1')

    def test_initial_images(self):
        fragment = AnonymousFragment.objects.create(name='name')
        self.assertEqual(fragment.images.count(), 0)

    def test_initial_topics(self):
        fragment = AnonymousFragment.objects.create(name='name')
        self.assertEqual(fragment.topics.count(), 0)

    def test_get_absolute_url(self):
        fragment = AnonymousFragment.objects.create(name='name')
        self.assertEqual(
            fragment.get_absolute_url(),
            reverse('anonymous_fragment:detail', kwargs={'pk': fragment.pk})
        )

    def test_get_display_name(self):
        # we need to show the name of the first citing work of original texts
        fragment = AnonymousFragment.objects.create(name='name')
        citing_work = CitingWork.objects.create(title='title')
        data = {
            'content': 'content',
            'citing_work': citing_work,
        }
        # it is unlinked so we show general
        OriginalText.objects.create(**data, owner=fragment)
        self.assertEqual(
            fragment.get_display_name(),
            'Anonymous F1'
        )

    def test_get_display_name_no_original_text(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.get_display_name(), str(fragment))
