from uuid import UUID

import pytest
from django.test import TestCase

from rard.research.models import Antiquarian, CommentableText

pytestmark = pytest.mark.django_db


class TestAntiquarian(TestCase):

    def test_creation(self):
        data = {
            'name': 'John Smith',
            're_code': '0000'
        }
        a = Antiquarian.objects.create(**data)
        for key, value in data.items():
            self.assertEqual(getattr(a, key), value)

    def test_required_fields(self):
        self.assertFalse(Antiquarian._meta.get_field('name').blank)
        self.assertTrue(Antiquarian._meta.get_field('works').blank)
        self.assertTrue(Antiquarian._meta.get_field('re_code').blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'John Smith',
            're_code': '2319'
        }
        a = Antiquarian(**data)
        self.assertEqual(str(a), data['name'])

    def test_primary_key(self):
        # check we are using uuids as primary keys
        a = Antiquarian(name='John Smith')
        self.assertIsInstance(a.pk, UUID)

        # check the reference is correct
        self.assertEqual(a.reference, a.pk.hex[:8])

    def test_no_initial_works(self):
        data = {
            'name': 'John Smith',
        }
        a = Antiquarian.objects.create(**data)
        self.assertEqual(a.works.count(), 0)

    def test_biography_created_with_antiquarian(self):
        data = {
            'name': 'John Smith',
        }
        a = Antiquarian.objects.create(**data)
        self.assertIsNotNone(a.biography.pk)
        self.assertEqual(
            CommentableText.objects.get(pk=a.biography.pk),
            a.biography
        )

    def test_biography_deleted_with_antiquarian(self):
        data = {
            'name': 'John Smith',
        }
        a = Antiquarian.objects.create(**data)
        biography_pk = a.biography.pk
        a.delete()
        with self.assertRaises(CommentableText.DoesNotExist):
            CommentableText.objects.get(pk=biography_pk)
