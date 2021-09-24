import pytest
from django.test import TestCase

from rard.research.models import Symbol, SymbolGroup

pytestmark = pytest.mark.django_db


class TestSymbolGroup(TestCase):
    def test_required_fields(self):
        # required on forms
        self.assertFalse(SymbolGroup._meta.get_field("name").blank)

    def test_display(self):
        NAME = "group"
        group = SymbolGroup.objects.create(name=NAME)
        self.assertEqual(group.name, NAME)
        self.assertEqual(str(group), NAME)


class TestSymbol(TestCase):
    def test_required_fields(self):
        # char code required on forms
        self.assertFalse(Symbol._meta.get_field("code").blank)

        # not required
        self.assertTrue(Symbol._meta.get_field("name").blank)
        self.assertTrue(Symbol._meta.get_field("group").null)

    def test_default_display(self):
        CODE = "0020"
        symbol = Symbol.objects.create(code=CODE)
        self.assertEqual(str(symbol), "Code: {}".format(CODE))

    def test_display_name_if_given(self):
        CODE = "0020"
        NAME = "Squiggle"
        symbol = Symbol.objects.create(code=CODE, name=NAME)
        self.assertEqual(str(symbol), NAME)
