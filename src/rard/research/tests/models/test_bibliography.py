import pytest
from django.test import TestCase

from rard.research.models import Antiquarian, BibliographyItem, TextObjectField

pytestmark = pytest.mark.django_db


class TestBibliography(TestCase):
    def setUp(self):
        self.parent_object = TextObjectField.objects.create(content="foo")

    def test_display(self):
        # the __str__ function should show the name
        data = {
            "authors": "Hartley, J. R.",
            "author_surnames": "Hartley",
            "title": "Fly Fishing",
            "year": "1855",
        }
        b = BibliographyItem(**data)
        self.assertEqual(str(b), "Hartley [1855]: Fly Fishing")

    def test_creation(self):
        data = {
            "authors": "Hartley, J. R.",
            "title": "Fly Fishing",
        }
        item = BibliographyItem.objects.create(**data)
        self.assertTrue(BibliographyItem.objects.filter(pk=item.pk).exists())

    def test_related_query_name_for_bib_item_fields(self):
        data = {
            "authors": "Hartley, J. R.",
            "title": "Fly Fishing",
        }
        item = BibliographyItem.objects.create(**data)
        self.assertTrue(BibliographyItem.objects.filter(pk=item.pk).exists())
        # self.assertEqual(self.parent_object.references.count(), 1)
        # text objects have a related query name to allow filtering of
        # bib items by the fact they point to text fields
        """self.assertEqual(
            BibliographyItem.objects.filter(
                text_fields__pk=self.parent_object.pk
            ).count(),
            1,
        )"""

    def test_bibliography_can_belong_to_multiple_antiquarians(self):
        # works can belong to multiple antiquarians
        data = {
            "authors": "Hartley, J. R.",
            "title": "Fly Fishing",
        }
        b = BibliographyItem.objects.create(**data)
        length = 10
        for counter in range(0, length):
            antiquarian = Antiquarian.objects.create(
                name="John Smith", re_code="smitre%03d" % counter
            )
            antiquarian.bibliography_items.add(b)

        self.assertEqual(b.antiquarian_set.count(), length)
