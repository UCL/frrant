from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import BibliographyItemForm
from rard.research.models import BibliographyItem
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class BibliographyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = BibliographyItem
    permission_required = ("research.view_bibliographyitem",)


class BibliographyDetailView(
    CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = BibliographyItem
    fields = (
        "authors",
        "author_surnames",
        "year",
        "title",
    )
    permission_required = ("research.view_bibliographyitem",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bibliography = self.get_object()
        antiquarians = bibliography.antiquarian_set.all()
        citing_authors = bibliography.citingauthor_set.all()
        context.update(
            {
                "bibliography": bibliography,
                "antiquarians": antiquarians,
                "citing_authors": citing_authors,
            }
        )
        return super().get_context_data(**kwargs)


class BibliographyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BibliographyItem
    template_name = "research/bibliographyitem_form.html"
    form_class = BibliographyItemForm
    success_url_name = "bibliography:detail"
    title = "Create Bibliography Item"
    # change_antiquarian only required when adding an Antiquarian to a Bibliography,
    # sim CitingAuthor
    permission_required = (
        "research.change_antiquarian",
        "research.add_bibliographyitem",
        "research.change_citingauthor",
    )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "title": self.title,
            }
        )
        return context

    def get_success_url(self, *args, **kwargs):
        return reverse("bibliography:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        rtn = super().form_valid(form)
        for a in form.cleaned_data["antiquarians"]:
            a.bibliography_items.add(self.object)
        for c in form.cleaned_data["citing_authors"]:
            c.bibliography_items.add(self.object)
        return rtn

    """def get_antiquarian(self, *args, **kwargs):
        # look for Antiquarian in the GET or POST parameters
        # in case this bibliography is created from there
        # use to add context
        self.antiquarian = None
        if self.request.method == "GET":
            antiquarian_pk = self.request.GET.get("antiquarian", None)
        elif self.request.method == "POST":
            antiquarian_pk = self.request.POST.get("antiquarian", None)
        if antiquarian_pk:
            try:
                self.antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
            except Antiquarian.DoesNotExist:
                raise Http404
        return self.antiquarian"""


class BibliographyUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):

    model = BibliographyItem
    template_name = "research/bibliographyitem_form.html"
    form_class = BibliographyItemForm
    title = "Edit Bibliography Item"

    permission_required = (
        "research.change_bibliographyitem",
        "research.change_antiquarian",
        "research.change_citingauthor",
    )

    def get_success_url(self, *args, **kwargs):
        return reverse("bibliography:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        bibliography = form.save(commit=False)
        updated = form.cleaned_data["antiquarians"]
        existing = bibliography.antiquarian_set.all()
        # get 2 lists of antiquarians, from which to add/remove this bibliography item
        to_remove = [a for a in existing if a not in updated]
        to_add = [a for a in updated if a not in existing]
        for a in to_remove:
            a.bibliography.remove(bibliography)
        for a in to_add:
            a.bibliography_items.add(bibliography)
        c_updated = form.cleaned_data["citing_authors"]
        c_existing = bibliography.citingauthor_set.all()
        # get 2 lists of citing_authors, from which to add/remove this bibliography item
        to_remove = [c for c in c_existing if c not in updated]
        to_add = [c for c in c_updated if c not in existing]
        for c in to_remove:
            c.bibliography.remove(bibliography)
        for c in to_add:
            c.bibliography_items.add(bibliography)
        return super().form_valid(form)

    """def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "title": self.title,
                "antiquarians": self.instance.antiquarian_set.all(),
            }
        )
        return context"""


@method_decorator(require_POST, name="dispatch")
class BibliographyDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):

    model = BibliographyItem
    success_url = reverse_lazy("bibliography:list")
    permission_required = ("research.delete_bibliographyitem",)
