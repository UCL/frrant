import pytest
from django.test import TestCase

from rard.research.models import (
    Antiquarian,
    BibliographyItem,
    Fragment,
    Testimonium,
    TextObjectField,
)

pytestmark = pytest.mark.django_db


class TestTextObjectField(TestCase):
    def test_required_fields(self):
        self.assertTrue(TextObjectField._meta.get_field("content").blank)

    def test_creation(self):
        text = TextObjectField.objects.create()
        self.assertTrue(TextObjectField.objects.filter(pk=text.pk).exists())

    def test_default_value(self):
        text = TextObjectField.objects.create()
        self.assertEqual(text.content, "")

    def test_stored_value(self):
        content = "some content"
        text = TextObjectField.objects.create(content=content)
        self.assertEqual(text.content, content)

    def test_display(self):
        content = "some content"
        text = TextObjectField.objects.create(content=content)
        self.assertEqual(str(text), content)

    def test_get_related_field_default(self):
        content = "some content"
        text = TextObjectField.objects.create(content=content)
        # no related object
        self.assertIsNone(text.get_related_object())
        # create antiquarian with this text as commentary
        related = Antiquarian.objects.create(name="name", introduction=text)
        # we have this as a commentary now
        self.assertEqual(text.get_related_object(), related)

    def test_antiquarian_property(self):
        related = Antiquarian.objects.create(name="name")
        self.assertEqual(related.introduction.antiquarian, related)
        self.assertIsNone(related.introduction.fragment)
        self.assertIsNone(related.introduction.testimonium)

    def test_fragment_property(self):
        related = Fragment.objects.create(name="name")
        self.assertEqual(related.commentary.fragment, related)
        self.assertIsNone(related.commentary.antiquarian)
        self.assertIsNone(related.commentary.testimonium)

    def test_testimonium_property(self):
        related = Testimonium.objects.create(name="name")
        self.assertEqual(related.commentary.testimonium, related)
        self.assertIsNone(related.commentary.antiquarian)
        self.assertIsNone(related.commentary.fragment)

    def test_bibliography_mentions_in_introduction_linked_to_antiquarian(self):
        """When BibliographyItems are mentioned in an Antiquarian
        Introduction, a link between those items and the Antiquarian
        should be created when it is saved."""
        mention_html = """
            <span class="mention" data-id="1" data-target="bibliographyitem">
                Test bibliography item
            </span>"""
        antiquarian = Antiquarian.objects.create(name="name")
        # ID should equal 1
        bibliography_item = BibliographyItem.objects.create(
            authors="The authors",
            author_surnames="Author1, Author2",
            year="888",
            title="There and back again",
        )
        antiquarian.introduction.content = mention_html
        antiquarian.introduction.save()
        # After saving the introduction, the bibliography item should have been
        # added to the antiquarian.bibliography_items
        self.assertEqual(antiquarian.bibliography_items.first(), bibliography_item)
