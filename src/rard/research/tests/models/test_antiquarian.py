import pytest
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, TextObjectField

pytestmark = pytest.mark.django_db


class TestAntiquarian(TestCase):

    def test_creation(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian.objects.create(**data)
        for key, value in data.items():
            self.assertEqual(getattr(a, key), value)

    def test_required_fields(self):
        self.assertFalse(Antiquarian._meta.get_field('name').blank)
        self.assertFalse(Antiquarian._meta.get_field('re_code').blank)
        self.assertTrue(Antiquarian._meta.get_field('works').blank)

    def test_unique_re_code(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        Antiquarian.objects.create(**data)
        # creating the same re code again should raise db error
        with self.assertRaises(IntegrityError):
            Antiquarian.objects.create(**data)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian(**data)
        self.assertEqual(str(a), data['name'])

    def test_no_initial_works(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian.objects.create(**data)
        self.assertEqual(a.works.count(), 0)

    def test_can_have_multiple_works(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian.objects.create(**data)
        length = 10
        for _ in range(0, length):
            a.works.create(name='name')
        self.assertEqual(a.works.count(), length)

    def test_biography_created_with_antiquarian(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian.objects.create(**data)
        self.assertIsNotNone(a.biography.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=a.biography.pk),
            a.biography
        )

    def test_biography_deleted_with_antiquarian(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian.objects.create(**data)
        biography_pk = a.biography.pk
        a.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=biography_pk)

    def test_order_by_name(self):
        names = [
            'Zippy',
            'George',
            'Bungle',
            'Geoffrey',
        ]
        for counter, name in enumerate(names):
            Antiquarian.objects.create(
                name=name, re_code='code{}'.format(counter)
            )

        db_names = []
        for a in Antiquarian.objects.all():
            db_names.append(a.name)

        self.assertEqual(db_names, sorted(names))

    def test_get_absolute_url(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian.objects.create(**data)
        self.assertEqual(
            a.get_absolute_url(),
            reverse('antiquarian:detail', kwargs={'pk': a.pk})
        )

    def test_display_date_range(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        a = Antiquarian.objects.create(**data)
        # check the default with nothing set
        self.assertEqual(
            a.display_date_range(),
            '-'
        )

        a.year_type = Antiquarian.YEAR_RANGE
        a.year1 = -10
        a.year2 = -2
        a.circa = False
        self.assertEqual(
            a.display_date_range(),
            'From 10 to 2 BC'
        )
        a.year2 = 20
        self.assertEqual(
            a.display_date_range(),
            'From 10 BC to 20 AD'
        )
        a.circa = True
        self.assertEqual(
            a.display_date_range(),
            'c. 10 BC to 20 AD'
        )
        a.year_type = Antiquarian.YEAR_AFTER
        a.circa = False
        self.assertEqual(
            a.display_date_range(),
            'After 10 BC'
        )
        a.circa = True
        self.assertEqual(
            a.display_date_range(),
            'After c. 10 BC'
        )
        a.year_type = Antiquarian.YEAR_BEFORE
        a.circa = False
        self.assertEqual(
            a.display_date_range(),
            'Before 10 BC'
        )
        a.circa = True
        self.assertEqual(
            a.display_date_range(),
            'Before c. 10 BC'
        )
        a.year_type = Antiquarian.YEAR_SINGLE
        self.assertEqual(
            a.display_date_range(),
            'c. 10 BC'
        )

    def test_bcad(self):
        # test the function that does BC/AD
        self.assertEqual(Antiquarian._bcad(-10), '10 BC')
        self.assertEqual(Antiquarian._bcad(0), '0 AD')
        self.assertEqual(Antiquarian._bcad(30), '30 AD')

        # handle null values gracefully
        self.assertEqual(Antiquarian._bcad(None), '')
        self.assertEqual(Antiquarian._bcad('bad value'), '')
