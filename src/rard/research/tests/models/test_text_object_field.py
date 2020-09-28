import pytest
from django.test import TestCase

from rard.research.models import TextObjectField

pytestmark = pytest.mark.django_db


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
