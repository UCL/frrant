import pytest
from django.db.utils import IntegrityError
from django.test import TestCase

from rard.research.models import (
    Antiquarian,
    CitingWork,
    Concordance,
    Fragment,
    OriginalText,
    Reference,
    Translation,
)
from rard.research.models.base import FragmentLink

pytestmark = pytest.mark.django_db


class TestOriginalText(TestCase):
    def setUp(self):
        self.fragment = Fragment.objects.create(name="name")
        self.citing_work = CitingWork.objects.create(title="title")

    def test_creation(self):
        data = {
            "content": "content",
            "citing_work": self.citing_work,
        }
        text = OriginalText.objects.create(**data, owner=self.fragment)
        for key, val in data.items():
            self.assertEqual(getattr(text, key), val)

    def test_required_fields(self):
        # required fields on forms
        self.assertFalse(OriginalText._meta.get_field("content").blank)

    def test_parent_object_required(self):
        data = {
            "content": "content",
            "citing_work": self.citing_work,
        }
        # cannot create an original text with no fragment
        with self.assertRaises(IntegrityError):
            OriginalText.objects.create(**data)

    def test_reference_order(self):
        data = {
            "content": "content",
            "citing_work": self.citing_work,
            "reference_order": "00001.00010.12345",
        }
        text = OriginalText.objects.create(**data, owner=self.fragment)
        self.assertEqual(text.remove_reference_order_padding(), "1.10.12345")


class TestConcordance(TestCase):
    def setUp(self):
        self.fragment = Fragment.objects.create(name="name")
        self.citing_work = CitingWork.objects.create(title="title")
        self.original_text = OriginalText.objects.create(
            owner=self.fragment, citing_work=self.citing_work
        )

    def test_creation(self):
        data = {
            "source": "source",
            "identifier": "identifier",
        }
        concordance = Concordance.objects.create(
            **data, original_text=self.original_text
        )
        for key, val in data.items():
            self.assertEqual(getattr(concordance, key), val)

    def test_required_fields(self):
        # required fields on forms
        self.assertFalse(Concordance._meta.get_field("source").blank)
        self.assertFalse(Concordance._meta.get_field("identifier").blank)

    def test_original_text_required(self):
        data = {
            "source": "source",
            "identifier": "identifier",
        }
        # cannot create a concordance with no original text
        with self.assertRaises(IntegrityError):
            Concordance.objects.create(**data)

    def test_concordance_identifiers(self):
        # test the names to go in the concordance table including ordinals
        # set up a second original text
        OriginalText.objects.create(owner=self.fragment, citing_work=self.citing_work)
        a = Antiquarian.objects.create(name="name1", re_code="name1")
        link = FragmentLink.objects.create(fragment=self.fragment, antiquarian=a)

        concordances = link.get_concordance_identifiers()
        self.assertEqual(
            [x[0] for x in self.original_text.concordances.all()], concordances
        )


class TestTranslation(TestCase):
    def setUp(self):
        fragment = Fragment.objects.create(name="name")
        citing_work = CitingWork.objects.create(title="title")
        self.original_text = OriginalText.objects.create(
            owner=fragment, citing_work=citing_work
        )

    def test_creation(self):
        data = {
            "translator_name": "translator_name",
            "translated_text": "translated_text",
        }
        translation = Translation.objects.create(
            **data, original_text=self.original_text
        )
        for key, val in data.items():
            self.assertEqual(getattr(translation, key), val)

    def test_required_fields(self):
        # required fields on forms
        self.assertFalse(Translation._meta.get_field("translator_name").blank)
        self.assertFalse(Translation._meta.get_field("translated_text").blank)

    def test_original_text_required(self):
        data = {
            "translator_name": "translator_name",
            "translated_text": "translated_text",
        }
        # cannot create a translation without an original text
        with self.assertRaises(IntegrityError):
            Translation.objects.create(**data)

    def test_approved_flag_default(self):
        data = {
            "translator_name": "translator_name",
            "translated_text": "translated_text",
        }
        translation = Translation.objects.create(
            **data, original_text=self.original_text
        )
        self.assertFalse(translation.approved)

    def test_approved_flag_reset(self):
        data = {
            "translator_name": "translator_name",
            "translated_text": "translated_text",
        }
        translation1 = Translation.objects.create(
            **data, original_text=self.original_text
        )
        translation2 = Translation.objects.create(
            **data, original_text=self.original_text
        )
        translation3 = Translation.objects.create(
            **data, original_text=self.original_text, approved=True
        )
        self.assertFalse(Translation.objects.get(pk=translation1.pk).approved)
        self.assertFalse(Translation.objects.get(pk=translation2.pk).approved)
        self.assertTrue(Translation.objects.get(pk=translation3.pk).approved)

        # set translation 1 to be approved
        translation1.approved = True
        translation1.save()

        # others should now be unapproved
        self.assertTrue(Translation.objects.get(pk=translation1.pk).approved)
        self.assertFalse(Translation.objects.get(pk=translation2.pk).approved)
        self.assertFalse(Translation.objects.get(pk=translation3.pk).approved)

        # creating an approved one should do the same
        translation4 = Translation.objects.create(
            **data, original_text=self.original_text, approved=True
        )
        self.assertFalse(Translation.objects.get(pk=translation1.pk).approved)
        self.assertFalse(Translation.objects.get(pk=translation2.pk).approved)
        self.assertFalse(Translation.objects.get(pk=translation3.pk).approved)
        self.assertTrue(Translation.objects.get(pk=translation4.pk).approved)


class TestCitingWork(TestCase):
    def test_creation(self):
        data = {
            "title": "title",
            "edition": "edition",
        }
        citing_work = CitingWork.objects.create(**data)
        for key, val in data.items():
            self.assertEqual(getattr(citing_work, key), val)

    def test_display(self):
        data = {
            "title": "title",
            "edition": "edition",
        }
        citing_work = CitingWork.objects.create(**data)
        self.assertEqual(str(citing_work), "Anonymous, {}".format(data["title"]))

    def test_no_edition_in_display(self):
        data = {
            "title": "title",
            "edition": "edition",
        }
        citing_work = CitingWork.objects.create(**data)
        self.assertFalse(str(citing_work).find(data["edition"]) >= 0)


class TestReferences(TestCase):
    def setUp(self):
        self.citing_work = CitingWork.objects.create(title="title")
        fragment = Fragment.objects.create(name="fragment_name")

        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=self.citing_work,
        )

        reference = "2.6-9"
        self.reference = Reference.objects.create(
            editor="superfluous",
            reference_position=reference,
            original_text=self.original_text,
        )

    def test_reference_creation(self):
        self.assertEqual(self.original_text.references.first(), self.reference)

    def test_reference_deletion(self):
        self.reference.delete()
        self.original_text.refresh_from_db()
        self.assertEqual(self.original_text.references.count(), 0)

    def test_reference_list_property(self):
        self.assertEqual(self.original_text.references.count(), 1)
        self.assertEqual(
            self.original_text.reference_list[0], self.reference.reference_position
        )
        self.reference2 = Reference.objects.create(
            editor="superfluous",
            reference_position="3.9.9",
            original_text=self.original_text,
        )
        references_list = ["superfluous 2.6-9 |", "superfluous 3.9.9 |"]
        self.assertEqual(self.original_text.references.count(), 2)
        self.assertIn("superfluous", self.original_text.reference_list[0])
        self.assertEqual(self.original_text.reference_list, references_list)
