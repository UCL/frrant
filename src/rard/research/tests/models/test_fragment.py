
import pytest
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from rard.research.models import Fragment, TextObjectField

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
        self.assertTrue(Fragment._meta.get_field('definite_works').blank)
        self.assertTrue(Fragment._meta.get_field('possible_works').blank)
        self.assertTrue(
            Fragment._meta.get_field('definite_antiquarians').blank
        )
        self.assertTrue(
            Fragment._meta.get_field('possible_antiquarians').blank
        )

    def test_name_unique(self):
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
        }
        fragment = Fragment.objects.create(**data)
        with self.assertRaises(IntegrityError):
            Fragment.objects.create(**data)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(str(fragment), data['name'])

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
