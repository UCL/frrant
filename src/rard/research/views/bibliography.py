from urllib import response
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import DeleteView, UpdateView
from django.urls import reverse
from django.http.response import Http404

from rard.research.models import BibliographyItem, Antiquarian
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bibliography = self.get_object()
        antiquarians = bibliography.antiquarian_set.all()
        context.update({
            "bibliography": bibliography,
            "antiquarians": antiquarians,
        })
        return super().get_context_data(**kwargs)

class BibliographyCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    template_name = "research/bibliographyitem_form.html"
    form_class = BibliographyItemForm
    success_url_name = "bibligraphy:detail"
    title = "Create Bibliography Item"
    # change_antiquarian only required when adding an Ant to a Bib
    permission_required = (
        "research.change_antiquarian",
        "research.add_bibliographyitem",
    )
    # The following should be fine, even if get_antiquarian() returns None
    check_lock_object = "antiquarian"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "title": self.title,
                "antiquarian": self.get_antiquarian(),
            }
        )
        return context
    
    def get_success_url(self):
        return reverse("bibliography:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        data = form.cleaned_data

    def get_antiquarian(self, *args, **kwargs):
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
        return self.antiquarian
    
    # def dispatch(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
    #    return super().dispatch(request, *args, **kwargs)
    #    # need to ensure the lock-checked attribute is initialised in dispatch
    #    self.get_antiquarian()
    #    return super().dispatch(*args, **kwargs)

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

    