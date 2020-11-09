import pytest
from django.test import TestCase

from rard.research.forms import BookForm

pytestmark = pytest.mark.django_db


class TestBookForm(TestCase):
    def test_number_and_subtitle_not_required(self):
        # allow the user to skip either and insist on the backend
        # that at least one of them is filled out
        form = BookForm()
        self.assertFalse(form.fields['number'].required)
        self.assertFalse(form.fields['subtitle'].required)

    def test_number_or_subtitle_required_on_backend(self):
        # should be invalid where both are blank
        data = {
            'number': '',
            'subtitle': '',
        }
        self.assertFalse(BookForm(data=data).is_valid())

        # we can specify number...
        data = {
            'number': '1',
            'subtitle': '',
        }
        self.assertTrue(BookForm(data=data).is_valid())

        # ... or subtitle
        data = {
            'number': '',
            'subtitle': 'This is the title',
        }
        self.assertTrue(BookForm(data=data).is_valid())
