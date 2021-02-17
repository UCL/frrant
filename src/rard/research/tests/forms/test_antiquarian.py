import pytest
from django.test import TestCase

from rard.research.forms import (AntiquarianDetailsForm,
                                 AntiquarianIntroductionForm)
from rard.research.models import Antiquarian

pytestmark = pytest.mark.django_db


class TestAntiquarianForms(TestCase):
    def test_introduction_not_required(self):

        form = AntiquarianIntroductionForm()
        self.assertFalse(form.fields['introduction_text'].required)

    def test_introduction_form_label(self):
        data = {
            'name': 'John Smith',
            're_code': '2319'
        }
        # create an antiquarian with a bio and check it is on the form
        antiquarian = Antiquarian.objects.create(**data)
        form = AntiquarianIntroductionForm(instance=antiquarian)
        self.assertEqual(
            form.fields['introduction_text'].label,
            'Introduction'
        )

    def test_re_code_label(self):
        form = AntiquarianDetailsForm()
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

        form = AntiquarianIntroductionForm(instance=antiquarian)
        self.assertEqual(form.fields['introduction_text'].initial, bio)

    def test_introduction_save(self):
        data = {
            'name': 'John Smith',
            're_code': '2319'
        }
        # create an antiquarian with a bio and check it is on the form
        antiquarian = Antiquarian.objects.create(**data)
        form_data = {
            'introduction_text': 'Something interesting'
        }
        form = AntiquarianIntroductionForm(
            instance=antiquarian, data=form_data
        )
        self.assertTrue(form.is_valid())
        antiquarian = form.save()

        self.assertEqual(
            antiquarian.introduction.content,
            form_data['introduction_text']
        )

    def test_date_range_saves(self):
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'dates_type': Antiquarian.DATES_LIVED,
            'year_type': Antiquarian.YEAR_RANGE,
            'year1': -10,
            'year2': -2
        }
        form = AntiquarianDetailsForm(data=data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()

        self.assertEqual(antiquarian.name, data['name'])
        self.assertEqual(antiquarian.re_code, data['re_code'])
        self.assertEqual(antiquarian.dates_type, data['dates_type'])
        self.assertEqual(antiquarian.year_type, data['year_type'])
        self.assertEqual(antiquarian.year1, data['year1'])
        self.assertEqual(antiquarian.year2, data['year2'])

    def test_bad_date_range(self):
        # make from date > to date
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'dates_type': Antiquarian.DATES_LIVED,
            'year_type': Antiquarian.YEAR_RANGE,
            'year1': -10,
            'year2': -20  # oops
        }
        form = AntiquarianDetailsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)
        self.assertIn("year1", form.errors)
        self.assertIn("year2", form.errors)

    def test_missing_dates_type(self):
        # if we specify some dates we need a dates type
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'year_type': Antiquarian.YEAR_RANGE,
            'year1': 10,
            'year2': 20
        }
        form = AntiquarianDetailsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("dates_type", form.errors)

    def test_missing_year_type(self):
        # if we specify some dates we need a dates type
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'dates_type': Antiquarian.DATES_LIVED,
            'year1': 10,
            'year2': 20
        }
        form = AntiquarianDetailsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("year_type", form.errors)

    def test_bad_value(self):
        # make from date > to date
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'dates_type': Antiquarian.DATES_LIVED,
            'year_type': Antiquarian.YEAR_RANGE,
            'year1': None,  # oops
            'year2': -20
        }
        form = AntiquarianDetailsForm(data=data)
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
                'dates_type': Antiquarian.DATES_LIVED,
                'year_type': year_type,
                'year1': -10,
                'year2': 20  # not needed but somehow set
            }
        form = AntiquarianDetailsForm(data=data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()
        self.assertEqual(antiquarian.year_type, data['year_type'])
        self.assertEqual(antiquarian.year1, data['year1'])
        self.assertEqual(antiquarian.year2, None)  # should be cleared
