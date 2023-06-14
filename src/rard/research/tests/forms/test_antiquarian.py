import pytest
from django.test import TestCase

from rard.research.forms import AntiquarianDetailsForm, AntiquarianIntroductionForm
from rard.research.models import Antiquarian

pytestmark = pytest.mark.django_db


class TestAntiquarianForms(TestCase):
    def test_introduction_not_required(self):
        form = AntiquarianIntroductionForm()
        self.assertFalse(form.fields["introduction_text"].required)

    def test_introduction_form_label(self):
        data = {"name": "John Smith", "re_code": "2319"}
        # create an antiquarian with a bio and check it is on the form
        antiquarian = Antiquarian.objects.create(**data)
        form = AntiquarianIntroductionForm(instance=antiquarian)
        self.assertEqual(form.fields["introduction_text"].label, "Introduction")

    def test_re_code_label(self):
        form = AntiquarianDetailsForm()
        self.assertEqual(form.fields["re_code"].label, "RE Number")

    def test_introduction_initial_value_update(self):
        data = {"name": "John Smith", "re_code": "2319"}
        # create an antiquarian with a bio and check it is on the form
        antiquarian = Antiquarian.objects.create(**data)
        bio = "Something interesting"
        antiquarian.introduction.content = bio

        form = AntiquarianIntroductionForm(instance=antiquarian)
        self.assertEqual(form.fields["introduction_text"].initial, bio)

    def test_introduction_save(self):
        data = {"name": "John Smith", "re_code": "2319"}
        # create an antiquarian with a bio and check it is on the form
        antiquarian = Antiquarian.objects.create(**data)
        form_data = {"introduction_text": "Something interesting"}
        form = AntiquarianIntroductionForm(instance=antiquarian, data=form_data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()

        self.assertEqual(
            antiquarian.introduction.content, form_data["introduction_text"]
        )

    def test_date_info_saves(self):
        data = {
            "name": "John Smith",
            "re_code": "2319",
            "date_range": "From then to now",
            "order_year": -234,
        }
        form = AntiquarianDetailsForm(data=data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()

        self.assertEqual(antiquarian.name, data["name"])
        self.assertEqual(antiquarian.re_code, data["re_code"])
        self.assertEqual(antiquarian.date_range, data["date_range"])
        self.assertEqual(antiquarian.order_year, data["order_year"])

    def test_date_info_optional(self):
        # if we specify some dates we need a dates type
        data = {
            "name": "John Smith",
            "re_code": "2319",
        }
        form = AntiquarianDetailsForm(data=data)
        self.assertTrue(form.is_valid())
