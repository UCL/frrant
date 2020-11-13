from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Symbol, SymbolGroup


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ('symbol_display', 'code', 'group', 'name', 'name_display')

    search_fields = ['code', 'name', 'group__name']

    class Media:
        css = {
            'all': ('css/alphabetum.css',)
            }

    def name_display(self, symbol):
        return symbol.get_display_name()
    name_display.short_description = 'Displayed Name'

    def symbol_display(self, symbol):
        return mark_safe(
            '<span class="alphabetum" '
            'style="font-size:large;">&#x{};</span>'.format(symbol.code)
        )
    symbol_display.short_description = 'Symbol'


@admin.register(SymbolGroup)
class SymbolGroupAdmin(admin.ModelAdmin):
    pass
