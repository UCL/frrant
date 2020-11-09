import pytest
from django.test import TestCase

from rard.research.forms import (FragmentCommentaryForm, FragmentForm,
                                 FragmentLinkWorkForm)
from rard.research.models import Antiquarian, Book, Fragment, Work

pytestmark = pytest.mark.django_db


class TestFragmentForm(TestCase):

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


class TestFragmentCommentaryForm(TestCase):

    def test_commentary_initial_value_update(self):
        fragment = Fragment.objects.create(name='name')
        commentary = 'Something interesting'
        fragment.commentary.content = commentary

        form = FragmentCommentaryForm(instance=fragment)
        self.assertEqual(form.fields['commentary_text'].initial, commentary)

    def test_commentary_save(self):
        fragment = Fragment.objects.create(name='fragment')

        data = {
            'commentary_text': 'Something interesting',
        }
        form = FragmentCommentaryForm(instance=fragment, data=data)

        self.assertTrue(form.is_valid())
        form.save()
        refetch = Fragment.objects.get(pk=fragment.pk)
        self.assertEqual(
            refetch.commentary.content,
            data['commentary_text']
        )


class TestFragmentLinkWorkForm(TestCase):

    def test_required_fields_no_work_selected(self):
        # if no work specified we have no books to select
        # and all the works are possible
        form = FragmentLinkWorkForm(work=None)
        self.assertIsNone(form.fields['work'].initial)
        self.assertTrue(form.fields['book'].disabled)
        self.assertEqual(form.fields['book'].queryset.count(), 0)

    def test_required_fields_with_work_selected(self):
        work = Work.objects.create(name='foo')
        NUM_BOOKS = 5
        for i in range(0, NUM_BOOKS):
            Book.objects.create(number=i, work=work)

        form = FragmentLinkWorkForm(work=work)
        self.assertEqual(form.fields['work'].initial, work)
        self.assertFalse(form.fields['book'].disabled)
        self.assertEqual(form.fields['book'].queryset.count(), NUM_BOOKS)
