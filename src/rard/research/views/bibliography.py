from itertools import permutations
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import BibliographyItemForm, BibliographyItemInlineForm
from rard.research.models import Antiquarian, BibliographyItem, TextObjectField
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class BibliographyOverviewView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = "research/bibliographyitem_overview.html"
    permission_required = ("research.view_bibliographyitem",)

    def get(self, request, *args, **kwargs):
        return render(self.request, template_name=self.template_name)


class BibliographyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = BibliographyItem
    permission_required = ("research.view_bibliographyitem",)
    template_name = "research/partials/htmx_bibliography_list_page.html"


class BibliographyDetailView(
    CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = BibliographyItem
    permission_required = ("research.view_bibliographyitem",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bibliography = self.get_object()
        antiquarians = bibliography.antiquarians.all()
        citing_authors = bibliography.citing_authors.all()
        context.update(
            {
                "bibliography": bibliography,
                "antiquarians": antiquarians,
                "citing_authors": citing_authors,
            }
        )
        return context


class BibliographyCreateInlineView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = BibliographyItem
    template_name = "research/inline_forms/bibliographyitem_form.html"
    form_class = BibliographyItemInlineForm
    permission_required = "research.add_bibliographyitem"

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message(
            self.request, messages.SUCCESS, f"{self.object} successfully created"
        )
        response = render(
            self.request,
            template_name="research/partials/inline_create_success.html",
            context=self.get_context_data(),
            status=200,
        )
        response["HX-Trigger"] = "new-item"
        return response


class BibliographyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BibliographyItem
    template_name = "research/bibliographyitem_form.html"
    form_class = BibliographyItemForm
    title = "Create Bibliography Item"
    # change_antiquarian only required when adding an Antiquarian to a Bibliography,
    # sim CitingAuthor
    permission_required = "research.add_bibliographyitem"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.title,
            }
        )
        return context

    def form_valid(self, form):
        rtn = super().form_valid(form)
        for a in form.cleaned_data["antiquarians"]:
            a.bibliography_items.add(self.object)
        for c in form.cleaned_data["citing_authors"]:
            c.bibliography_items.add(self.object)
        return rtn


class BibliographyUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = BibliographyItem
    template_name = "research/bibliographyitem_form.html"
    form_class = BibliographyItemForm
    title = "Edit Bibliography Item"

    permission_required = ("research.change_bibliographyitem",)

    def get_success_url(self, *args, **kwargs):
        return reverse("bibliography:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        bibliography = form.save(commit=False)
        updated = form.cleaned_data["antiquarians"]
        existing = bibliography.antiquarians.all()
        # get 2 lists of antiquarians, from which to add/remove this bibliography item
        to_remove = [a for a in existing if a not in updated]
        to_add = [a for a in updated if a not in existing]
        for a in to_remove:
            a.bibliography_items.remove(bibliography)
        for a in to_add:
            a.bibliography_items.add(bibliography)
        c_updated = form.cleaned_data["citing_authors"]
        c_existing = bibliography.citing_authors.all()
        # get 2 lists of citing_authors, from which to add/remove this bibliography item
        to_remove = [c for c in c_existing if c not in updated]
        to_add = [c for c in c_updated if c not in existing]
        for c in to_remove:
            c.bibliography_items.remove(bibliography)
        for c in to_add:
            c.bibliography_items.add(bibliography)
        return super().form_valid(form)

    """def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "title": self.title,
                "antiquarians": self.instance.antiquarians.all(),
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

    def delete(self, request, *args, **kwargs):
        """
        if a TextObjectField contains a mention of a BibilographyItem,
        it will contain this string:
        <span class="mention" data-denotation-char="@" data-id="20" data-index="1" data-target="bibliographyitem"  # noqa: E501
        data-index is the order within the TextObjectField, so we can ignore
        data-id is the bibliography_item.pk
        note that the attributes can come in any order, hence the slightly convoluted regex builder (re doesn't support DEFINE)  # noqa: E501
        """
        bibliography = self.get_object()
        bib_pk = bibliography.pk

        p = [
            r"class=\"mention\" ",
            r"data-denotation-char=\"@\" ",
            rf"data-id=\"{bib_pk}\" ",
            # r'data-index="[0-9]{1,4}" ',  # we can ignore this and use .{0,17} instead
            r"data-target=\"bibliographyitem\" ",
        ]
        list_of_short_patterns = list(permutations(p))
        pattern_to_find = ""
        for c, t in enumerate(list_of_short_patterns):
            # iterate tuples in l
            if c > 0:
                pattern_to_find += "|"
            pattern_to_find += (
                "<span " + t[0] + ".{0,17}" + t[1] + ".{0,17}" + t[2] + ".{0,17}" + t[3]
            )

        bib_mention_count = TextObjectField.objects.filter(
            content__regex=pattern_to_find
        ).count()

        if bib_mention_count > 0:
            # There are @mentions of this bibliography_item, so do something:
            s = "s" if bib_mention_count > 1 else ""
            messages.add_message(
                self.request,
                messages.ERROR,
                "This Bibliography item has "
                + str(bib_mention_count)
                + " mention"
                + s
                + " elsewhere in the database, deletion not successful",
            )
            return HttpResponseRedirect(
                reverse("bibliography:detail", kwargs={"pk": bib_pk})
            )
        else:
            return super().delete(self, request, *args, **kwargs)


class BibliographySectionView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = BibliographyItem
    template_name = "research/partials/antiquarian_bibliography_list.html"
    context_object_name = "bibliography_items"
    permission_required = ("research.view_bibliographyitem",)

    def get_queryset(self) -> QuerySet[Any]:
        if self.model is not None:
            queryset = self.model._default_manager.all()
        self.ant_pk = self.kwargs.get("pk")
        if self.ant_pk:
            queryset = queryset.filter(antiquarians__id=self.ant_pk)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.ant_pk:
            context["antiquarian"] = Antiquarian.objects.get(id=self.ant_pk)
        return context
