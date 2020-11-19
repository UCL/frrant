import pytest
from django.test import TestCase

from rard.research.forms import AntiquarianForm
from rard.research.models import Antiquarian

pytestmark = pytest.mark.django_db


class TestAntiquarianForm(TestCase):
    def test_introduction_not_required(self):

        form = AntiquarianForm()
        self.assertFalse(form.fields['introduction_text'].required)

    def test_introduction_form_label(self):
        form = AntiquarianForm()
        self.assertEqual(form.fields['introduction_text'].label, 'Introduction')

    def test_re_code_label(self):
        form = AntiquarianForm()
        self.assertEqual(form.fields['re_code'].label, 'RE Number')

    def test_introduction_initial_value_update(self):
        data = {
            'name': 'John Smith',
            're_code': '2319'
        }
        # create an antiquarian with a bio and check it is on the form
        antiquarian = Antiquarian.objects.create(**data)
        bio = 'Something interesting'
        antiquarian.introduction.content = bio

        form = AntiquarianForm(instance=antiquarian)
        self.assertEqual(form.fields['introduction_text'].initial, bio)

    def test_introduction_save(self):
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'introduction_text': 'Something interesting'
        }
        form = AntiquarianForm(data=data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()

        self.assertEqual(antiquarian.name, data['name'])
        self.assertEqual(antiquarian.re_code, data['re_code'])
        self.assertEqual(antiquarian.introduction.content, data['introduction_text'])

    def test_date_range_saves(self):
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'year_type': Antiquarian.YEAR_RANGE,
            'year1': -10,
            'year2': -2
        }
        form = AntiquarianForm(data=data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()

        self.assertEqual(antiquarian.name, data['name'])
        self.assertEqual(antiquarian.re_code, data['re_code'])
        self.assertEqual(antiquarian.year_type, data['year_type'])
        self.assertEqual(antiquarian.year1, data['year1'])
        self.assertEqual(antiquarian.year2, data['year2'])

    def test_bad_date_range(self):
        # make from date > to date
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'year_type': Antiquarian.YEAR_RANGE,
            'year1': -10,
            'year2': -20  # oops
        }
        form = AntiquarianForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)
        self.assertIn("year1", form.errors)
        self.assertIn("year2", form.errors)

    def test_bad_value(self):
        # make from date > to date
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'year_type': Antiquarian.YEAR_RANGE,
            'year1': None,  # oops
            'year2': -20
        }
        form = AntiquarianForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("year1", form.errors)

    def test_before_after_single_clears_year2(self):
        for year_type in (
                Antiquarian.YEAR_BEFORE,
                Antiquarian.YEAR_AFTER,
                Antiquarian.YEAR_SINGLE):
            # make from date > to date
            data = {
                'name': 'John Smith',
                're_code': '2319',
                'year_type': year_type,
                'year1': -10,
                'year2': 20  # not needed but somehow set
            }
        form = AntiquarianForm(data=data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()
        self.assertEqual(antiquarian.year_type, data['year_type'])
        self.assertEqual(antiquarian.year1, data['year1'])
        self.assertEqual(antiquarian.year2, None)  # should be cleared
