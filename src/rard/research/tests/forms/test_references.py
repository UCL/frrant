import pytest
from django.test import TestCase

from rard.research.forms import ReferenceFormset
from rard.research.models import CitingWork, Fragment, OriginalText, Reference

pytestmark = pytest.mark.django_db


class TestReferenceFormset(TestCase):
    def setUp(self):
        self.fragment = Fragment.objects.create(name="name")
        self.citing_work = CitingWork.objects.create(title="title")
        ot_data = {
            "content": "content",
            "citing_work": self.citing_work,
            "owner": self.fragment,
        }
        self.original_text = OriginalText.objects.create(**ot_data)
        self.reference1 = Reference.objects.create(
            original_text=self.original_text,
            editor="Romulus",
            reference_position="1.2.3",
        )
        self.reference2 = Reference.objects.create(
            original_text=self.original_text, editor="Remus", reference_position="4.5.6"
        )

    def test_reference_formset_initial_values(self):
        formset = ReferenceFormset(instance=self.original_text)
        # formset should include forms for both existing references
        initial_data = [form.initial for form in formset.forms]
        ref1_expected = {
            "editor": "Romulus",
            "reference_position": "1.2.3",
            "original_text": self.original_text.id,
        }
        ref2_expected = {
            "editor": "Remus",
            "reference_position": "4.5.6",
            "original_text": self.original_text.id,
        }
        self.assertIn(ref1_expected, initial_data)
        self.assertIn(ref2_expected, initial_data)

    def test_reference_formset_create(self):
        # Confirm there are two references initially
        self.assertEqual(self.original_text.references.count(), 2)

        # Create another reference attached to the original text
        data = {
            "references-TOTAL_FORMS": 1,
            "references-INITIAL_FORMS": 0,
            "references-MIN_NUM_FORMS": 0,
            "references-MAX_NUM_FORMS": 1000,
            "references-0-id": "",
            "references-0-original_text": self.original_text.id,
            "references-0-editor": "Numa",
            "references-0-reference_position": "3.2.1",
        }
        formset = ReferenceFormset(data=data, instance=self.original_text)
        if formset.is_valid():
            formset.save()

        # There should now be three references
        self.assertEqual(self.original_text.references.count(), 3)

    def test_reference_formset_update(self):
        new_ref_pos = "7.8.9"
        data = {
            "references-TOTAL_FORMS": 1,
            "references-INITIAL_FORMS": 1,  # Must be >0 if updating
            "references-MIN_NUM_FORMS": 0,
            "references-MAX_NUM_FORMS": 1000,
            "references-0-id": self.reference1.id,
            "references-0-original_text": self.original_text.id,
            "references-0-editor": self.reference1.editor,
            "references-0-reference_position": new_ref_pos,
        }
        formset = ReferenceFormset(data=data, instance=self.original_text)
        self.assertEqual(formset.is_valid(), True)
        if formset.is_valid():
            formset.save()
        self.reference1.refresh_from_db()
        self.assertEqual(self.reference1.reference_position, new_ref_pos)
