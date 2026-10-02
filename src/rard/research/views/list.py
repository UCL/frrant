"""An alternate ListView that avoids pagination when distilling."""
import django.views.generic


class ListView(django.views.generic.ListView):
    """List View that paginates only with authorized users."""

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.
        """
        if self.request.user.is_authenticated:
            return self.paginate_by
        return 9999999
