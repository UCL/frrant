from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import (
    ConcordanceModelCreateForm,
    ConcordanceModelSearchForm,
    ConcordanceModelUpdateForm,
    EditionForm,
)
from rard.research.models import ConcordanceModel, Edition, OriginalText, PartIdentifier
from rard.research.models.antiquarian import Antiquarian
from rard.research.models.bibliography import BibliographyItem
from rard.research.models.original_text import Concordance
from rard.research.models.work import Work
from rard.research.views.mixins import CheckLockMixin


def fetch_works(request):
    antiquarian = request.GET.get("antiquarian")
    works = Work.objects.filter(antiquarian=antiquarian)

    empty_option = '<option value="">Select work</option>'

    # Create options for each work
    work_options = "".join(
        [f'<option value="{work.id}">{work.name}</option>' for work in works]
    )

    options = empty_option + work_options
    return HttpResponse(options)


def fetch_parts(request):
    edition = request.GET.get("edition")
    parts = PartIdentifier.objects.filter(edition=edition)

    empty_option = '<option value="">Select identifier</option>'

    # Create options for each work
    part_options = "".join(
        [
            f'<option value="{part.id}">{part.value}</option>'
            for part in parts
            if not part.is_template
        ]
    )

    options = empty_option + part_options
    return HttpResponse(options)


def get_part_format(edition):
    """Get the first part identifier that is a template for the given edition.
    If no template exists, raise a DatabaseError since all Editions should have
    a template."""
    first_part = (
        PartIdentifier.objects.filter(edition=edition).filter(is_template=True).first()
    )
    if first_part:
        return first_part
    else:
        raise DatabaseError(f"No template part identifier exists for edition {edition}")


def create_edition_bib_item(pk):
    edition = Edition.objects.get(pk=pk)
    BibliographyItem.objects.create(
        authors=edition.name, author_surnames=edition.name, title=edition.description
    )


class ConcordanceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "research.view_concordance"
    model = ConcordanceModel
    template_name = "research/concordance_list.html"
    context_object_name = "concordance_list"
    form_class = ConcordanceModelSearchForm
    sort_by_antiquarian = True

    def post(self, request, *args, **kwargs):
        antiquarian = request.POST.get("antiquarian", None)
        work = request.POST.get("work", None)
        identifier = request.POST.get("identifier", None)
        edition = request.POST.get("edition", None)
        if any([antiquarian, work, identifier, edition]):
            queryset = self.get_queryset()
            context = self.get_context_data(results=queryset)
            return render(
                request, "research/partials/concordance_search_results.html", context
            )

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()  # all concordance models
        antiquarian_pk = self.request.POST.get("antiquarian", None)
        work_pk = self.request.POST.get("work", None)
        identifier_pk = self.request.POST.get("identifier", None)
        edition_pk = self.request.POST.get("edition", None)
        results_qs = []

        if antiquarian_pk:
            # get all links that are associated with that antiquarian, regardless of concordances
            antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
            results = list(antiquarian.testimonia.all()) + list(
                antiquarian.ordered_fragments()
            )
            filtered_concordances = [
                concordance
                for concordance in queryset
                if antiquarian in concordance.antiquarians
            ]
            results_qs = {"frrant": results, "concordances": filtered_concordances}

            if work_pk:
                # work can only be selected if antiquarian has been selected
                work = Work.objects.get(pk=work_pk)
                results = list(work.all_testimonia()) + list(work.all_fragments())
                filtered_concordances = [
                    concordance for concordance in queryset if work in concordance.works
                ]
                results_qs = {"frrant": results, "concordances": filtered_concordances}

        elif edition_pk:
            # also sort by this rather than by the frrant thing
            self.sort_by_antiquarian = False
            if edition_pk:
                results_qs = ConcordanceModel.get_ordered_queryset(
                    queryset.filter(identifier__edition=edition_pk)
                )
                if (
                    identifier_pk
                ):  # Identifier should not be an option without an edition
                    results_qs = ConcordanceModel.get_ordered_queryset(
                        queryset.filter(identifier=identifier_pk)
                    )
        else:
            results_qs = queryset.none()

        return results_qs

    def get_context_data(self, **kwargs):
        self.object_list = self.queryset
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class
        if self.sort_by_antiquarian is True:
            context["ant_sort"] = True
        return context


class ConcordanceEditionView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, View
):
    check_lock_object = "top_level_object"
    model = Edition
    permission_required = ("research.add_edition",)
    form_class = EditionForm
    template_name = "research/concordancemodel_form.html"

    def get_original_text(self, *args, **kwargs):
        if not getattr(self, "original_text", False):
            self.original_text = get_object_or_404(
                OriginalText, pk=self.kwargs.get("pk", None)
            )
        return self.original_text

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_original_text().owner

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        edition_form = EditionForm()
        original_text = self.get_original_text()

        edition = kwargs.get("edition", None)
        context = {
            "edition_form": edition_form,
            "concordance_form": None,
            "original_text": original_text,
            "edition": edition,
        }
        return render(
            request,
            self.template_name,
            context=context,
        )

    def post(self, request, *args, **kwargs):
        edition = request.POST.get("edition", None)
        new_edition = request.POST.get("new_edition", None)
        original_text = request.POST.get("original_text", self.get_original_text().pk)
        part_format = request.POST.get("part_format", None)

        edition_form = EditionForm(request.POST)
        if edition_form.is_valid():
            if new_edition:
                if not part_format:
                    part_format = "[none]"

                if not (part_format.startswith("[") and part_format.endswith("]")):
                    part_format = f"[{part_format}]"

                """create a new edition and template PI"""
                new_edition_instance = Edition.objects.create(
                    name=edition_form.cleaned_data["new_edition"],
                    description=edition_form.cleaned_data["new_description"],
                )
                new_edition_instance.save()

                pi = PartIdentifier.objects.create(
                    edition=new_edition_instance, value=part_format
                )
                part_format = pi.pk

                edition = new_edition_instance.pk
                create_edition_bib_item(edition)

            if not part_format:
                # set the part_format as the template part for the selected edition
                part_format = get_part_format(edition).pk

            return redirect(
                reverse(
                    "concordance:create_s2",
                    kwargs={
                        "ot_pk": original_text,
                        "e_pk": edition,
                        "p_pk": part_format,
                    },
                )
            )
        else:
            # form not valid
            return render(
                request,
                "research/partials/concordancemodel_form.html",
                {"edition_form": edition_form},
            )


class ConcordanceCreateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    check_lock_object = "top_level_object"

    # create a concordance for an original text
    model = ConcordanceModel
    permission_required = ("research.add_concordance",)
    form_class = ConcordanceModelCreateForm

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_original_text().owner

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        edition = self.kwargs.get("e_pk", None)
        part_format = self.kwargs.get("p_pk", None)
        concordance_form = ConcordanceModelCreateForm(
            edition=edition, part_format=part_format
        )
        return render(
            request,
            "research/partials/concordance_form_section.html",
            context=self.get_context_data(
                concordance_form=concordance_form,
                ediiton=edition,
                part_format=part_format,
            ),
        )

    def post(self, request, *args, **kwargs):
        edition = request.POST.get("edition", self.kwargs.get("e_pk"))
        new_identifier = request.POST.get("new_identifier", None)
        identifier = request.POST.get("identifier", None)

        if (
            new_identifier is not None
            and new_identifier.startswith("[")
            and new_identifier.endswith("]")
        ):
            new_identifier = new_identifier[1:-1]

        concordance_form = ConcordanceModelCreateForm(request.POST)
        if concordance_form.is_valid():
            if new_identifier:
                new_identifier_instance = PartIdentifier.objects.create(
                    edition=Edition.objects.get(pk=edition),
                    value=concordance_form.cleaned_data["new_identifier"],
                    display_order=concordance_form.cleaned_data["display_order"],
                )
                new_identifier_instance.save()
                identifier = new_identifier_instance.pk
            elif identifier is None:
                identifier = get_part_format(edition).pk
            self.form_valid(concordance_form, identifier=identifier)
            return redirect(self.get_success_url())
        else:
            # not valid
            concordance_form.cleaned_data["identifier"] = identifier
            edition = Edition.objects.get(pk=edition)
            part_format = get_part_format(edition)
            return render(
                request,
                "research/concordancemodel_form.html",
                context=self.get_context_data(
                    concordance_form=concordance_form,
                    edition=edition,
                    part_format=part_format,
                ),
            )

    def get_success_url(self, *args, **kwargs):
        return self.original_text.owner.get_absolute_url()

    def form_valid(self, form, *args, **kwargs):
        self.original_text = self.get_original_text()
        concordance = form.save(commit=False)
        concordance.identifier = PartIdentifier.objects.get(pk=kwargs["identifier"])
        # for some reason this doesn't get picked up when there's a new_identifier
        concordance.original_text = self.original_text
        return super().form_valid(form)

    def get_original_text(self, *args, **kwargs):
        if not getattr(self, "original_text", False):
            self.original_text = get_object_or_404(
                OriginalText, pk=self.kwargs.get("ot_pk", None)
            )
        return self.original_text

    def get_context_data(
        self,
        concordance_form=None,
        *args,
        **kwargs,
    ):
        original_text = self.get_original_text()
        edition_pk = self.kwargs.get("e_pk")
        pf_pk = self.kwargs.get("p_pk")
        edition = Edition.objects.get(pk=edition_pk)
        part_format = PartIdentifier.objects.get(pk=pf_pk)

        return {
            "concordance_form": concordance_form,
            "original_text": original_text,
            "request_action": reverse(
                "concordance:create_s2",
                kwargs={
                    "ot_pk": original_text.pk,
                    "e_pk": edition_pk,
                    "p_pk": pf_pk,
                },
            ),
            "part_format": part_format,
            "edition": edition,
        }


class ConcordanceUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    # this doesn't redirect to the owner when done
    check_lock_object = "top_level_object"

    model = ConcordanceModel
    form_class = ConcordanceModelUpdateForm
    permission_required = ("research.change_concordance",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.object = self.get_object()
        self.top_level_object = self.object.original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        edition = self.object.identifier.edition
        part_format = edition.get_part_format()
        context.update(
            {
                "original_text": self.object.original_text,
                "concordance_form": ConcordanceModelUpdateForm(instance=self.object),
                "is_update": True,
                "request_action": reverse(
                    "concordance:update", kwargs={"pk": self.object.pk}
                ),
                "part_format": part_format,
                "edition": edition,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        super().post(self, request, *args, **kwargs)
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()


@method_decorator(require_POST, name="dispatch")
class ConcordanceDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    check_lock_object = "top_level_object"

    model = ConcordanceModel
    permission_required = ("research.delete_concordance",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()


@method_decorator(require_POST, name="dispatch")
class OldConcordanceDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    check_lock_object = "top_level_object"

    model = Concordance
    permission_required = ("research.delete_concordance",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()
