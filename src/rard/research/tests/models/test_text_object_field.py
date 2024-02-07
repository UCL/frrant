import pytest
from django.test import TestCase

from rard.research.models import (
    Antiquarian,
    BibliographyItem,
    Fragment,
    Testimonium,
    TextObjectField,
)
from rard.research.models.fragment import AnonymousFragment

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
        antiquarian = Antiquarian.objects.create(name="name", re_code="bibant")
        # ID should equal 1
        bibliography_item = BibliographyItem.objects.create(
            authors="The authors",
            author_surnames="Author1, Author2",
            year="888",
            title="There and back again",
        )
        mention_html = (
            f"<span class='mention' data-id='{bibliography_item.id}'"
            "data-target='bibliographyitem'>Test bibliography item</span>"
        )
        antiquarian.introduction.content = mention_html
        antiquarian.introduction.save()
        # After saving the introduction, the bibliography item should have been
        # added to the antiquarian.bibliography_items
        self.assertEqual(antiquarian.bibliography_items.first(), bibliography_item)

    def test_update_mentions(self):
        """When an (Anonymous) Fragment or Testimonium gets mentioned in an introduction or commentary,
        upon saving, the mentions should be identified and relevant links should be created
        """
        antiquarian = Antiquarian.objects.create(name="a1", re_code="mentionsant")
        fragment = Fragment.objects.create(name="f1")
        anon_frag = AnonymousFragment.objects.create(name="af1")
        testimonium = Testimonium.objects.create(name="t1")

        mention_html = (
            f"<span class='mention' data-id='{fragment.id}'"
            "data-target='fragment'>Test fragment mention</span>"
            f"<span class='mention' data-id='{anon_frag.id}'"
            "data-target='anonymousfragment'>Test anonymus fragment mention</span>"
            f"<span class='mention' data-id='{testimonium.id}'"
            "data-target='testimonium'>Test testimonium mention</span>"
        )
        antiquarian.introduction.content = mention_html
        antiquarian.introduction.save()
        ftm = antiquarian.introduction.fragment_testimonia_mentions
        # check the items are in the fragment_testimonia_mentions of TOF
        self.assertEqual(len(ftm), 3)
        self.assertIn(fragment, ftm)
        self.assertIn(anon_frag, ftm)
        self.assertIn(testimonium, ftm)
        # check the reverse relationship via m2m was established
        self.assertIn((antiquarian, "antiquarian"), fragment.mentioned_in_list)
        self.assertIn((antiquarian, "antiquarian"), anon_frag.mentioned_in_list)
        self.assertIn((antiquarian, "antiquarian"), testimonium.mentioned_in_list)

        mention_html = (
            f"<span class='mention' data-id='{fragment.id}'"
            "data-target='fragment'>Test fragment mention</span>"
        )
        antiquarian.introduction.content = mention_html
        antiquarian.introduction.save()
        ftm = antiquarian.introduction.fragment_testimonia_mentions
        # check the items are in the fragment_testimonia_mentions of TOF
        self.assertEqual(len(ftm), 1)
        self.assertIn(fragment, ftm)
        self.assertNotIn(anon_frag, ftm)
        self.assertNotIn(testimonium, ftm)
        # check the reverse relationship via m2m was established
        self.assertIn((antiquarian, "antiquarian"), fragment.mentioned_in_list)
        self.assertNotIn((antiquarian, "antiquarian"), anon_frag.mentioned_in_list)
        self.assertNotIn((antiquarian, "antiquarian"), testimonium.mentioned_in_list)
