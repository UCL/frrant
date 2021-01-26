from unittest import skip

import pytest
from django.test import TestCase

from rard.research.models import (Antiquarian, Fragment, Testimonium,
                                  TextObjectField)

pytestmark = pytest.mark.django_db


@skip("Functionality to be deleted")
class TestTextObjectField(TestCase):

    def test_required_fields(self):
        self.assertTrue(TextObjectField._meta.get_field('content').blank)

    def test_creation(self):
        text = TextObjectField.objects.create()
        self.assertTrue(TextObjectField.objects.filter(pk=text.pk).exists())

    def test_default_value(self):
        text = TextObjectField.objects.create()
        self.assertEqual(text.content, '')

    def test_stored_value(self):
        content = 'some content'
        text = TextObjectField.objects.create(content=content)
        self.assertEqual(text.content, content)

    def test_display(self):
        content = 'some content'
        text = TextObjectField.objects.create(content=content)
        self.assertEqual(str(text), content)

    def test_get_related_field_default(self):
        content = 'some content'
        text = TextObjectField.objects.create(content=content)
        # no related object
        self.assertIsNone(text.get_related_object())
        # create antiquarian with this text as commentary
        related = Antiquarian.objects.create(name='name', introduction=text)
        # we have this as a commentary now
        self.assertEqual(text.get_related_object(), related)

    def test_antiquarian_property(self):
        related = Antiquarian.objects.create(name='name')
        self.assertEqual(related.introduction.antiquarian, related)
        self.assertIsNone(related.introduction.fragment)
        self.assertIsNone(related.introduction.testimonium)

    def test_fragment_property(self):
        related = Fragment.objects.create(name='name')
        self.assertEqual(related.commentary.fragment, related)
        self.assertIsNone(related.commentary.antiquarian)
        self.assertIsNone(related.commentary.testimonium)

    def test_testimonium_property(self):
        related = Testimonium.objects.create(name='name')
        self.assertEqual(related.commentary.testimonium, related)
        self.assertIsNone(related.commentary.antiquarian)
        self.assertIsNone(related.commentary.fragment)
