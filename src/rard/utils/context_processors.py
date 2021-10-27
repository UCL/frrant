from django.conf import settings

from rard.research.models import Symbol, SymbolGroup


def settings_context(_request):
    """Settings available by default to the templates context."""
    # Note: we intentionally do NOT expose the entire settings
    # to prevent accidental leaking of sensitive information
    return {
        "DEBUG": settings.DEBUG,
        "PRODUCTION_INSTANCE": settings.PRODUCTION_INSTANCE,
    }


def symbols_context(_request):
    """Symbols available to the symbol picker on each page."""
    return {
        "all_symbols": Symbol.objects.all(),
        "symbol_groups": SymbolGroup.objects.all(),
    }
