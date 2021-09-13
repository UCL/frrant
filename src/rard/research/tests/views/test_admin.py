import pytest
from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.utils.safestring import mark_safe

from rard.research.admin import SymbolAdmin
from rard.research.models import Symbol

pytestmark = pytest.mark.django_db


class TestSymbolAdmin(TestCase):

    # Test creation of new user via the admin interface
    def setUp(self):
        site = AdminSite()
        self.admin_view = SymbolAdmin(Symbol, site)

    def test_name_display(self):
        symbol = Symbol.objects.create(code="0020")
        self.assertEqual(
            self.admin_view.name_display(symbol), symbol.get_display_name()
        )

    def test_symbol_display(self):
        symbol = Symbol.objects.create(code="0020")
        expected = mark_safe(
            '<span class="alphabetum" '
            'style="font-size:large;">&#x{};</span>'.format(symbol.code)
        )
        self.assertEqual(self.admin_view.symbol_display(symbol), expected)
