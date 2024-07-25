from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import (
    ConcordanceModelCreateForm,
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
from rard.research.models.original_text import Concordance
from rard.research.views.mixins import CheckLockMixin


class ConcordanceListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "research.view_concordance"

    def get(self, request, *args, **kwargs):
        """Create a complete list of concordances for display in a table. Each row
        requires:
        - a display name derived from a fragment link
        - url for the relevant fragment/anonymous fragment
        - a set of concordances related to the original text
        The same row will be repeated once for each fragment link associated with an
        original text's owner, but with a different name in the frrant column.
        If a fragment has more than one original text, concordances will be listed for
        each original text separately with an ordinal value appended to the fragment
        link names; e.g. "Quintus Ennius F8a" and "Quintus Ennius F8b"
        """

        # Get every original text instance that has at least one associated concordance
        original_text_queryset = (
            OriginalText.objects.filter(concordances__isnull=False)
            .distinct()
            .prefetch_related("owner", "concordances")
        )

        # Original texts should appear once for each work link
        concordances_table_data = []
        for ot in original_text_queryset:
            concordances = ot.concordances.all()
            identifiers = (
                ot.concordance_identifiers
            )  # Get list of names from work links
            owner_url = ot.owner.get_absolute_url()
            if identifiers:  # Where a link exists for the original text owner
                for frrant in identifiers:
                    concordances_table_data.append(
                        {
                            "frrant": {"url": owner_url, "display_name": frrant},
                            "concordances": concordances,
                        }
                    )
            else:  # Use the fragment's name as the frrant display name
                concordances_table_data.append(
                    {
                        "frrant": {
                            "url": owner_url,
                            "display_name": ot.owner.get_display_name(),
                        },
                        "concordances": concordances,
                    }
                )
        concordances_table_data.sort(key=lambda i: i["frrant"]["display_name"])

        # Paginate on the table data
        paginator = Paginator(concordances_table_data, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Calculate the maximum number of concordances for a single original text
        # so we know how wide to make the table
        items = [len(row["concordances"]) for row in page_obj]
        max_length = max(items) if items else 0

        context_data = {"column_range": range(0, max_length), "page_obj": page_obj}
        return render(request, "research/concordance_list.html", context_data)


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
        print(concordance, concordance.pk, concordance.original_text)
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
        **kwargs
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
        self.top_level_object = self.get_object().original_text.owner
        self.object = self.get_object()
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
