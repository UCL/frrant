import pytest
from django.db.utils import IntegrityError
from django.test import TestCase

from rard.research.models import BibliographyItem, TextObjectField

pytestmark = pytest.mark.django_db


class TestBibliography(TestCase):

    def setUp(self):
        self.parent_object = TextObjectField.objects.create(content='foo')

    def test_creation(self):
        data = {
            'author': 'Hartley, J. R.',
            'title': 'Fly Fishing',
            'page': '1',
            'parent': self.parent_object
        }
        item = BibliographyItem.objects.create(**data)
        self.assertTrue(BibliographyItem.objects.filter(pk=item.pk).exists())

    def test_parent_required(self):
        data = {
            'author': 'Hartley, J. R.',
            'title': 'Fly Fishing',
            'page': '1'
        }
        # cannot create a comment with no parent
        with self.assertRaises(IntegrityError):
            BibliographyItem.objects.create(**data)

    def test_delete_parent_deletes_item(self):
        data = {
            'author': 'Hartley, J. R.',
            'title': 'Fly Fishing',
            'page': '1',
            'parent': self.parent_object
        }
        item = BibliographyItem.objects.create(**data)
        self.assertTrue(BibliographyItem.objects.filter(pk=item.pk).exists())
        self.parent_object.delete()
        # NB this is only true when a GenericRelation exists on the
        # parent model
        self.assertFalse(BibliographyItem.objects.filter(pk=item.pk).exists())

    def test_related_query_name_for_bib_item_fields(self):
        data = {
            'author': 'Hartley, J. R.',
            'title': 'Fly Fishing',
            'page': '1',
            'parent': self.parent_object
        }
        item = BibliographyItem.objects.create(**data)
        self.assertTrue(BibliographyItem.objects.filter(pk=item.pk).exists())
        self.assertEqual(self.parent_object.references.count(), 1)
        # text objects have a related query name to allow filtering of
        # bib items by the fact they point to text fields
        self.assertEqual(
            BibliographyItem.objects.filter(
                text_fields__pk=self.parent_object.pk
            ).count(), 1)
