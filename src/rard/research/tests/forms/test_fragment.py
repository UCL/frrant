import pytest
from django.test import TestCase

from rard.research.forms import FragmentForm
from rard.research.models import Fragment

pytestmark = pytest.mark.django_db


class TestFragmentForm(TestCase):
    def test_commentary_initial_value_update(self):
        data = {
            'name': 'name',
        }
        # create an antiquarian with a bio and check it is on the form
        fragment = Fragment.objects.create(**data)
        commentary = 'Something interesting'
        fragment.commentary.content = commentary

        form = FragmentForm(instance=fragment)
        self.assertEqual(form.fields['commentary_text'].initial, commentary)
