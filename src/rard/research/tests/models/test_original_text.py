from uuid import UUID

import pytest
from django.db.utils import IntegrityError
from django.test import TestCase

from rard.research.models import (Concordance, Fragment, OriginalText,
                                  Translation)

pytestmark = pytest.mark.django_db


class TestOriginalText(TestCase):

    def setUp(self):
        self.fragment = Fragment.objects.create(name='name')

    def test_creation(self):
        # can create with a name only
        data = {
            'title': 'title',
            'content': 'content',
            'apparatus_criticus': 'apparatus_criticus',
        }
        text = OriginalText.objects.create(**data, fragment=self.fragment)
        for key, val in data.items():
            self.assertEqual(getattr(text, key), val)

    def test_required_fields(self):
        # required fields on forms
        self.assertFalse(OriginalText._meta.get_field('title').blank)
        self.assertFalse(OriginalText._meta.get_field('content').blank)
        # optional fields on forms
        self.assertTrue(
            OriginalText._meta.get_field('apparatus_criticus').blank
        )

    def test_primary_key(self):
        # check we are using uuids as primary keys
        data = {
            'title': 'title',
            'content': 'content',
            'apparatus_criticus': 'apparatus_criticus',
        }
        text = OriginalText.objects.create(**data, fragment=self.fragment)
        self.assertIsInstance(text.pk, UUID)

    def test_fragment_required(self):
        data = {
            'title': 'title',
            'content': 'content',
            'apparatus_criticus': 'apparatus_criticus',
        }
        # cannot create an original text with no fragment
        with self.assertRaises(IntegrityError):
            OriginalText.objects.create(**data)


class TestConcordance(TestCase):

    def setUp(self):
        fragment = Fragment.objects.create(name='name')
        self.original_text = OriginalText.objects.create(fragment=fragment)

    def test_creation(self):
        data = {
            'source': 'source',
            'identifier': 'identifier',
        }
        concordance = Concordance.objects.create(
            **data,
            original_text=self.original_text
        )
        for key, val in data.items():
            self.assertEqual(getattr(concordance, key), val)

    def test_required_fields(self):
        # required fields on forms
        self.assertFalse(Concordance._meta.get_field('source').blank)
        self.assertFalse(Concordance._meta.get_field('identifier').blank)

    def test_primary_key(self):
        # check we are using uuids as primary keys
        data = {
            'source': 'source',
            'identifier': 'identifier',
        }
        concordance = Concordance.objects.create(
            **data,
            original_text=self.original_text
        )
        self.assertIsInstance(concordance.pk, UUID)

    def test_original_text_required(self):
        data = {
            'source': 'source',
            'identifier': 'identifier',
        }
        # cannot create a concordance with no original text
        with self.assertRaises(IntegrityError):
            Concordance.objects.create(**data)


class TestTranslation(TestCase):

    def setUp(self):
        fragment = Fragment.objects.create(name='name')
        self.original_text = OriginalText.objects.create(fragment=fragment)

    def test_creation(self):
        data = {
            'translator_name': 'translator_name',
            'translated_text': 'translated_text',
        }
        translation = Translation.objects.create(
            **data,
            original_text=self.original_text
        )
        for key, val in data.items():
            self.assertEqual(getattr(translation, key), val)

    def test_required_fields(self):
        # required fields on forms
        self.assertFalse(Translation._meta.get_field('translator_name').blank)
        self.assertFalse(Translation._meta.get_field('translated_text').blank)

    def test_primary_key(self):
        # check we are using uuids as primary keys
        data = {
            'translator_name': 'translator_name',
            'translated_text': 'translated_text',
        }
        translation = Translation.objects.create(
            **data,
            original_text=self.original_text
        )
        self.assertIsInstance(translation.pk, UUID)

    def test_original_text_required(self):
        data = {
            'translator_name': 'translator_name',
            'translated_text': 'translated_text',
        }
        # cannot create a translation without an original text
        with self.assertRaises(IntegrityError):
            Translation.objects.create(**data)
