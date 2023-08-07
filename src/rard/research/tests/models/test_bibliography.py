import pytest
from django.test import TestCase

from rard.research.models import Antiquarian, BibliographyItem

pytestmark = pytest.mark.django_db


class TestBibliography(TestCase):
    def setUp(self):
        data = {
            "authors": "Hartley, J. R.",
            "author_surnames": "Hartley",
            "title": "Fly Fishing",
            "year": "1855",
        }
        self.bibliography = BibliographyItem.objects.create(**data)

    def test_display(self):
        # the __str__ function should show the name
        self.assertEqual(str(self.bibliography), "Hartley [1855]: Fly Fishing")

    def test_creation(self):
        self.assertTrue(
            BibliographyItem.objects.filter(pk=self.bibliography.pk).exists()
        )

    def test_bibliography_can_belong_to_multiple_antiquarians(self):
        # works can belong to multiple antiquarians
        length = 10
        for counter in range(0, length):
            antiquarian = Antiquarian.objects.create(
                name="John Smith", re_code="smitre%03d" % counter
            )
            antiquarian.bibliography_items.add(self.bibliography)

        self.assertEqual(self.bibliography.antiquarians.count(), length)
