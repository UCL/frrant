import pytest
from django.test import TestCase

from rard.research.forms import AntiquarianForm
from rard.research.models import Antiquarian

pytestmark = pytest.mark.django_db


class TestAntiquarianForm(TestCase):
    def test_biography_not_required(self):

        form = AntiquarianForm()
        self.assertFalse(form.fields['biography_text'].required)

    def test_biography_form_label(self):
        form = AntiquarianForm()
        self.assertEqual(form.fields['biography_text'].label, 'Biography')

    def test_re_code_label(self):
        form = AntiquarianForm()
        self.assertEqual(form.fields['re_code'].label, 'RE Code')

    def test_biography_initial_value_update(self):
        data = {
            'name': 'John Smith',
            're_code': '2319'
        }
        # create an antiquarian with a bio and check it is on the form
        antiquarian = Antiquarian.objects.create(**data)
        bio = 'Something interesting'
        antiquarian.biography.content = bio

        form = AntiquarianForm(instance=antiquarian)
        self.assertEqual(form.fields['biography_text'].initial, bio)

    def test_biography_save(self):
        data = {
            'name': 'John Smith',
            're_code': '2319',
            'biography_text': 'Something interesting'
        }
        form = AntiquarianForm(data=data)
        self.assertTrue(form.is_valid())
        antiquarian = form.save()

        self.assertEqual(antiquarian.name, data['name'])
        self.assertEqual(antiquarian.re_code, data['re_code'])
        self.assertEqual(antiquarian.biography.content, data['biography_text'])
