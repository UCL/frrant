
import pytest
from django.test import TestCase
from django.urls import reverse

from rard.research.models import (CitingWork, Fragment, OriginalText,
                                  TextObjectField)

pytestmark = pytest.mark.django_db


class TestFragment(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(fragment.name, data['name'])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(Fragment._meta.get_field('name').blank)

        # not required on forms
        self.assertTrue(Fragment._meta.get_field('apparatus_criticus').blank)
        self.assertTrue(Fragment._meta.get_field('images').blank)
        self.assertTrue(Fragment._meta.get_field('topics').blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(str(fragment), 'Fragment {}'.format(fragment.pk))

    def test_initial_images(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.images.count(), 0)

    def test_initial_topics(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.topics.count(), 0)

    def test_commentary_created(self):
        fragment = Fragment.objects.create(name='name')
        self.assertIsNotNone(fragment.commentary.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=fragment.commentary.pk),
            fragment.commentary
        )

    def test_commentary_deleted(self):
        fragment = Fragment.objects.create(name='name')
        commentary_pk = fragment.commentary.pk
        fragment.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=commentary_pk)

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
            'apparatus_criticus': 'apparatus_criticus',
            'citing_work': citing_work,
        }
        OriginalText.objects.create(**data, owner=fragment)
        self.assertEqual(
            fragment.get_display_name(),
            citing_work
        )
        # add a second citing work and we should indicate it
        citing_work = CitingWork.objects.create(title='title')
        data = {
            'content': 'content',
            'apparatus_criticus': 'apparatus_criticus',
            'citing_work': citing_work,
        }
        OriginalText.objects.create(**data, owner=fragment)
        self.assertEqual(
            fragment.get_display_name(),
            '{} +1 more'.format(citing_work)
        )

    def test_get_display_name_no_original_text(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.get_display_name(), str(fragment))
