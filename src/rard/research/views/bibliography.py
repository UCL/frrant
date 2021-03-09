from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.models import BibliographyItem
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class BibliographyListView(LoginRequiredMixin,
                           PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = BibliographyItem
    permission_required = ('research.view_bibliographyitem',)


class BibliographyUpdateView(CheckLockMixin, LoginRequiredMixin,
                             PermissionRequiredMixin, UpdateView):

    # the view attribute that needs to be checked for a lock
    check_lock_object = 'parent'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.parent = self.get_object().parent
        return super().dispatch(request, *args, **kwargs)

    model = BibliographyItem
    fields = ('authors', 'author_surnames', 'year', 'title',)
    permission_required = ('research.change_bibliographyitem',)

    def get_success_url(self, *args, **kwargs):
        return self.parent.get_absolute_url()


@method_decorator(require_POST, name='dispatch')
class BibliographyDeleteView(CheckLockMixin, LoginRequiredMixin,
                             PermissionRequiredMixin, DeleteView):

    check_lock_object = 'parent'

    model = BibliographyItem

    permission_required = (
        'research.delete_bibliographyitem',
    )

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.parent = self.get_object().parent
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.parent.get_absolute_url()
