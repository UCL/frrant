import pytest
from django.test import TestCase

from rard.research.forms import (
    FragmentCommentaryForm,
    FragmentLinkWorkForm,
    FragmentPublicCommentaryForm,
)
from rard.research.models import (
    Antiquarian,
    Book,
    Fragment,
    PublicCommentaryMentions,
    Work,
)

pytestmark = pytest.mark.django_db


class TestFragmentCommentaryForm(TestCase):
    def test_commentary_initial_value_update(self):
        fragment = Fragment.objects.create(name="name")
        commentary = "Something interesting"
        fragment.commentary.content = commentary

        form = FragmentCommentaryForm(instance=fragment)
        self.assertEqual(form.fields["commentary_text"].initial, commentary)

    def test_commentary_save(self):
        fragment = Fragment.objects.create(name="fragment")

        data = {
            "commentary_text": "Something interesting",
        }
        form = FragmentCommentaryForm(instance=fragment, data=data)

        self.assertTrue(form.is_valid())
        form.save()
        refetch = Fragment.objects.get(pk=fragment.pk)
        self.assertEqual(refetch.commentary.content, data["commentary_text"])


class TestFragmentPublicCommentaryForm(TestCase):
    def test_public_commentary_initial_value_update(self):
        fragment = Fragment.objects.create(name="name")
        public_commentary = PublicCommentaryMentions.objects.create(
            content="Something interesting"
        )
        fragment.public_commentary_mentions = public_commentary

        form = FragmentPublicCommentaryForm(instance=fragment)
        self.assertEqual(
            form.fields["commentary_text"].initial, public_commentary.content
        )

    def test_public_commentary_save(self):
        fragment = Fragment.objects.create(name="fragment")

        data = {
            "commentary_text": "Something interesting",
        }
        form = FragmentPublicCommentaryForm(instance=fragment, data=data)

        self.assertTrue(form.is_valid())
        form.save()
        refetch = Fragment.objects.get(pk=fragment.pk)
        self.assertEqual(
            refetch.public_commentary_mentions.content, data["commentary_text"]
        )


class TestFragmentLinkWorkForm(TestCase):
    def test_required_fields_no_antiquarian_selected(self):
        # if no antiquarian specified we have no works to select
        form = FragmentLinkWorkForm(
            antiquarian=None,
            work=None,
            book=None,
            definite_antiquarian=False,
            definite_work=False,
            update=False,
        )
        self.assertIsNone(form.fields["antiquarian"].initial)
        self.assertIsNone(form.fields["work"].initial)
        self.assertTrue(form.fields["work"].disabled)
        self.assertEqual(form.fields["work"].queryset.count(), 0)
        self.assertTrue(form.fields["book"].disabled)
        self.assertEqual(form.fields["book"].queryset.count(), 0)

    def test_required_fields_no_work_selected(self):
        antiquarian = Antiquarian.objects.create(name="Me", re_code=1)
        work = Work.objects.create(name="foo")
        antiquarian.works.add(work)
        form = FragmentLinkWorkForm(
            antiquarian=antiquarian,
            work=None,
            book=None,
            definite_antiquarian=False,
            definite_work=False,
            update=False,
        )
        self.assertEqual(form.fields["antiquarian"].initial, antiquarian)
        self.assertIsNone(form.fields["work"].initial)
        self.assertFalse(form.fields["work"].disabled)
        self.assertEqual(
            form.fields["work"].queryset.count(), 2
        )  # includes unknown work
        self.assertTrue(form.fields["book"].disabled)
        self.assertEqual(form.fields["book"].queryset.count(), 0)

    def test_required_fields_with_work_selected(self):
        antiquarian = Antiquarian.objects.create(name="Me", re_code=1)
        # this will automatically create an Unknown Book
        work = Work.objects.create(name="foo")

        NUM_BOOKS = 5
        for i in range(NUM_BOOKS):
            Book.objects.create(number=i, work=work)

        form = FragmentLinkWorkForm(
            antiquarian=antiquarian,
            work=work,
            book=None,
            definite_antiquarian=False,
            definite_work=False,
            update=False,
        )
        self.assertEqual(form.fields["antiquarian"].initial, antiquarian)
        self.assertEqual(form.fields["work"].initial, work)
        self.assertFalse(form.fields["book"].disabled)
        self.assertEqual(form.fields["book"].queryset.count(), NUM_BOOKS + 1)
