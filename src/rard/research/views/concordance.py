from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import (
    ConcordanceModelCreateForm,
    ConcordanceModelSearchForm,
    ConcordanceModelUpdateForm,
    EditionForm,
)
from rard.research.models import (
    AnonymousFragment,
    ConcordanceModel,
    Edition,
    Fragment,
    OriginalText,
    PartIdentifier,
)
from rard.research.models.antiquarian import Antiquarian
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
        # print("queryset", queryset)
        antiquarian_pk = self.request.POST.get("antiquarian", None)
        work_pk = self.request.POST.get("work", None)
        identifier_pk = self.request.POST.get("identifier", None)
        edition_pk = self.request.POST.get("edition", None)
        results_qs = []

        # form = ConcordanceModelSearchForm(self.request.POST)
        if antiquarian_pk:
            # get all links that are associated with that antiquarian, regardless of concordances
            antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
            results = list(antiquarian.testimonia.all()) + list(
                antiquarian.ordered_fragments().order_by("name")
            )
            filtered_concordances = [
                concordance
                for concordance in queryset
                if antiquarian in concordance.antiquarians
            ]
            results_qs = {"frrant": results, "concordances": filtered_concordances}

            if work_pk:
                print("work pk")
                # work can only be selected if antiquarian has been selected
                work = Work.objects.get(pk=work_pk)
                results_qs = work.all_testimonia().union(work.all_fragments())

        elif edition_pk or identifier_pk:
            # also sort by this rather than by the frrant thing
            self.sort_by_antiquarian = False
            if edition_pk:
                results_qs = queryset.filter(edition=edition_pk)
            if identifier_pk:
                results_qs = queryset.filter(identifier=identifier_pk)

        else:
            results_qs = queryset.none()

        print(results_qs)
        return results_qs

    def get_context_data(self, **kwargs):
        print("context kwargs", kwargs)

        self.object_list = self.queryset
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class
        if self.sort_by_antiquarian is True:
            context["ant_sort"] = True
        return context


class ConcordanceCreateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    check_lock_object = "top_level_object"

    # create a concordance for an original text
    model = ConcordanceModel
    permission_required = ("research.add_concordance",)
    form_class = ConcordanceModelCreateForm
    template_name = "research/concordancemodel_form.html"

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_original_text().owner
        if not isinstance(self.get_original_text().owner, Fragment) and not isinstance(
            self.get_original_text().owner, AnonymousFragment
        ):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        edition_form = EditionForm()
        concordance_form = None
        return render(
            request,
            self.template_name,
            context=self.get_context_data(edition_form, concordance_form),
        )

    def post(self, request, *args, **kwargs):
        is_concordance = request.POST.get("concordance", False)
        edition = request.POST.get("edition", None)
        new_edition = request.POST.get("new_edition", None)
        if is_concordance:
            # if it's the concordance submission (second stage)
            new_identifier = request.POST.get("new_identifier", None)
            identifier = request.POST.get("identifier", None)
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

                self.form_valid(concordance_form, identifier=identifier)
                return redirect(self.get_success_url())
            else:
                concordance_form.cleaned_data["identifier"] = identifier
                req_edition = request.POST.get("edition")
                edition_description = Edition.objects.get(pk=req_edition).description
                # not sure why it's not valid, also when it rerenders it doesn't have the edition
                return self.render_to_response(
                    self.get_context_data(
                        concordance_form=concordance_form,
                        edition_description=edition_description,
                    )
                )

        else:
            # if submitting edition (first stage)
            if edition or new_edition:
                edition_form = EditionForm(request.POST)
                if edition_form.is_valid():
                    if new_edition:
                        new_edition_instance = Edition.objects.create(
                            name=edition_form.cleaned_data["new_edition"],
                            description=edition_form.cleaned_data["new_description"],
                        )

                        new_edition_instance.save()

                        edition = new_edition_instance

                        edition_description = new_edition_instance.description
                    else:
                        edition_description = edition_form.cleaned_data[
                            "edition"
                        ].description

                concordance_form = ConcordanceModelCreateForm(request.POST, edition)

                context = self.get_context_data(
                    edition_form,
                    concordance_form,
                    edition_description=edition_description,
                )
                return render(
                    request, "research/partials/concordance_form_section.html", context
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
                OriginalText, pk=self.kwargs.get("pk", None)
            )
        return self.original_text

    def get_context_data(
        self,
        edition_form=None,
        concordance_form=None,
        edition_description=None,
        *args,
        **kwargs,
    ):
        return {
            "edition_form": edition_form,
            "concordance_form": concordance_form,
            "original_text": self.get_original_text(),
            "edition_description": edition_description,
            "post_url": reverse(
                "concordance:create", kwargs={"pk": self.get_original_text().pk}
            ),
        }


class ConcordanceUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
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
        context.update(
            {
                "original_text": self.object.original_text,
                "concordance_form": ConcordanceModelUpdateForm(instance=self.object),
                "is_update": True,
            }
        )
        return context

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
