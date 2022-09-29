from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.models import BibliographyItem
from rard.research.views.mixins import CheckLockMixin

from rard.research.forms import BibliographyItemForm

class BibliographyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = BibliographyItem
    permission_required = ("research.view_bibliographyitem",)

class BibliographyDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = BibliographyItem
    fields = (
        "authors",
        "author_surnames",
        "year",
        "title",
    )
    permission_required = ("research.view_bibliographyitem",)

class BibliographyCreateView(
    LoginRequiredMixin, PermissionRequiredMixin
):
    template_name = "research/bibliographyitem_form.html"
    form_class = BibliographyItemForm
    success_url_name = "bibligraphy:detail"
    title = "Create Bibliography Item"
    permission_required = ("research.add_bibliographyitem",)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({"title": self.title})
        return context

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

    