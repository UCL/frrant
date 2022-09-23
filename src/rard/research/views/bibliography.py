from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.models import BibliographyItem
from rard.research.views.mixins import CheckLockMixin


class BibliographyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = BibliographyItem
    permission_required = ("research.view_bibliographyitem",)


class BibliographyUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):

    
    model = BibliographyItem
    fields = (
        "authors",
        "author_surnames",
        "year",
        "title",
    )
    permission_required = ("research.change_bibliographyitem",)

    

@method_decorator(require_POST, name="dispatch")
class BibliographyDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):

    model = BibliographyItem

    permission_required = ("research.delete_bibliographyitem",)

    