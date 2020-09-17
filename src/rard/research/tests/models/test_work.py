from uuid import UUID

import pytest
from django.test import TestCase

from rard.research.models import Work

pytestmark = pytest.mark.django_db


class TestAntiquarian(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        for key, val in data.items():
            self.assertEqual(getattr(work, key), val)

    def test_required_fields(self):
        self.assertFalse(Work._meta.get_field('name').blank)
        self.assertFalse(Work._meta.get_field('subtitle').blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work(**data)
        self.assertEqual(str(work), data['name'])

    def test_primary_key(self):
        # check we are using uuids as primary keys
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work(**data)
        self.assertIsInstance(work.pk, UUID)
