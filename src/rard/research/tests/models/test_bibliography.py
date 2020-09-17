from uuid import UUID

import pytest
from django.db.utils import IntegrityError
from django.test import TestCase

from rard.research.models import BibliographyItem, CommentableText

pytestmark = pytest.mark.django_db


class TestBibliography(TestCase):

    def setUp(self):
        self.commentable = CommentableText.objects.create(content='foo')

    def test_creation(self):
        data = {
            'author': 'Hartley, J. R.',
            'title': 'Fly Fishing',
            'page': '1',
            'parent': self.commentable
        }
        item = BibliographyItem.objects.create(**data)
        self.assertIsInstance(item.pk, UUID)

    def test_parent_required(self):
        data = {
            'author': 'Hartley, J. R.',
            'title': 'Fly Fishing',
            'page': '1'
        }
        # cannot create a comment with no parent
        with self.assertRaises(IntegrityError):
            BibliographyItem.objects.create(**data)
