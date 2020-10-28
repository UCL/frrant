import pytest
from django.test import TestCase

from rard.research.forms import FragmentForm
from rard.research.models import Antiquarian, Fragment

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

    def test_links_save(self):

        a = Antiquarian.objects.create(name='namea', re_code='namea')
        b = Antiquarian.objects.create(name='nameb', re_code='nameb')
        fragment = Fragment.objects.create(name='name', apparatus_criticus='a')

        data = {
            'definite_antiquarians': (a.pk,),
            'possible_antiquarians': (b.pk,),
        }

        form = FragmentForm(instance=fragment, data=data)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(
            [x.pk for x in fragment.definite_antiquarians()],
            [x.pk for x in Antiquarian.objects.filter(pk=a.pk)]
        )
        self.assertEqual(
            [x.pk for x in fragment.possible_antiquarians()],
            [x.pk for x in Antiquarian.objects.filter(pk=b.pk)]
        )
