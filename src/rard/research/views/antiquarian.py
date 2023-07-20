from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import (
    AntiquarianCreateForm,
    AntiquarianDetailsForm,
    AntiquarianIntroductionForm,
    AntiquarianUpdateWorksForm,
    WorkForm,
)
from rard.research.models import Antiquarian, AntiquarianConcordance, Book, Work
from rard.research.views.mixins import (
    CanLockMixin,
    CheckLockMixin,
    DateOrderMixin,
    TextObjectFieldUpdateMixin,
)


class AntiquarianListView(
    DateOrderMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView
):
    paginate_by = 10
    model = Antiquarian
    permission_required = ("research.view_antiquarian",)


class AntiquarianDetailView(
    CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = Antiquarian
    permission_required = ("research.view_antiquarian",)

    def post(self, *args, **kwargs):
        link_pk = self.request.POST.get("link_id", None)
        work_pk = self.request.POST.get("work_id", None)
        antiquarian_pk = self.request.POST.get("antiquarian_id", None)
        object_type = self.request.POST.get("object_type", None)
        if work_pk:
            # moving a work up in the collection
            try:
                work = Work.objects.get(pk=work_pk)
                antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
                link = antiquarian.worklink_set.get(work=work)

                if "work_up" in self.request.POST:
                    link.move_to(link.order - 1)
                elif "work_down" in self.request.POST:
                    link.down()
                    link.move_to(link.order + 1)
            except (Work.DoesNotExist, KeyError):
                pass

        if link_pk and object_type:
            from rard.research.models.base import (
                AppositumFragmentLink,
                FragmentLink,
                TestimoniumLink,
            )

            model_classes = {
                "fragment": FragmentLink,
                "anonymous_fragment": AppositumFragmentLink,
                "testimonium": TestimoniumLink,
            }
            try:
                model_class = model_classes[object_type]
                link = model_class.objects.get(pk=link_pk)
                if "up_by_book" in self.request.POST:
                    link.move_to_by_book(link.order_in_book - 1)
                elif "down_by_book" in self.request.POST:
                    link.move_to_by_book(link.order_in_book + 1)

            except (ObjectDoesNotExist, KeyError):
                pass
        return HttpResponseRedirect(self.request.path)


class MoveLinkView(LoginRequiredMixin, View):
    render_partial_template = "research/partials/ordered_work_area.html"

    def render_valid_response(self, antiquarian):
        template = self.render_partial_template
        context = {
            "antiquarian": antiquarian,
            "has_object_lock": True,
            "can_edit": True,
            "perms": PermWrapper(self.request.user),
        }
        html = render_to_string(template, context)
        ajax_data = {"status": 200, "html": html}
        return JsonResponse(data=ajax_data, safe=False)

    def render_valid_work_response(self, work):
        template = "research/partials/ordered_book_area.html"
        context = {
            "work": work,
            "has_object_lock": True,
            "can_edit": True,
            "perms": PermWrapper(self.request.user),
            "ordered_materials": work.get_ordered_materials(),
        }
        html = render_to_string(template, context)
        ajax_data = {"status": 200, "html": html}
        return JsonResponse(data=ajax_data, safe=False)

    def post(self, *args, **kwargs):
        """if passed a book pk and link pk, we'd want to see if there's an option to 'move to' and apply it to the book/link"""
        link_pk = self.request.POST.get("link_id", None)
        work_pk = self.request.POST.get("work_id", None)
        book_pk = self.request.POST.get("book_id", None)
        antiquarian_pk = self.request.POST.get("antiquarian_id", None)

        if antiquarian_pk:
            antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
        object_type = self.request.POST.get("object_type", None)

        if book_pk:
            # moving a book wrt its work
            try:
                book = Book.objects.get(pk=book_pk)
                if "move_to" in self.request.POST:
                    pos = int(self.request.POST.get("move_to"))
                    book.move_to(pos)

            except (Book.DoesNotExist, KeyError):
                raise Http404

            return self.render_valid_work_response(book.work)

        if work_pk:
            # moving a work in the collection
            try:
                work = Work.objects.get(pk=work_pk)
                link = antiquarian.worklink_set.get(work=work)

                if "move_to" in self.request.POST:
                    pos = int(self.request.POST.get("move_to"))
                    link.move_to(pos)

            except (Work.DoesNotExist, KeyError):
                raise Http404

            return self.render_valid_response(antiquarian)

        if link_pk and object_type:
            from rard.research.models.base import (
                AppositumFragmentLink,
                FragmentLink,
                TestimoniumLink,
            )

            model_classes = {
                "fragment": FragmentLink,
                "anonymous_fragment": AppositumFragmentLink,
                "testimonium": TestimoniumLink,
            }

            try:
                model_class = model_classes[object_type]
                link = model_class.objects.get(pk=link_pk)
                work = link.work
                if "move_to_by_book" in self.request.POST:
                    pos = int(self.request.POST.get("move_to_by_book"))
                    link.move_to_by_book(pos)

            except (ObjectDoesNotExist, KeyError):
                raise Http404

            return self.render_valid_work_response(work)

        raise Http404


class AntiquarianCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Antiquarian
    permission_required = ("research.add_antiquarian",)
    form_class = AntiquarianCreateForm

    def get_success_url(self, *args, **kwargs):
        return reverse("antiquarian:detail", kwargs={"pk": self.object.pk})


class AntiquarianUpdateView(
    LoginRequiredMixin, CheckLockMixin, PermissionRequiredMixin, UpdateView
):
    model = Antiquarian
    permission_required = ("research.change_antiquarian",)
    form_class = AntiquarianDetailsForm


class AntiquarianUpdateIntroductionView(
    TextObjectFieldUpdateMixin, AntiquarianUpdateView
):
    model = Antiquarian
    permission_required = ("research.change_antiquarian",)
    form_class = AntiquarianIntroductionForm
    hx_trigger = "intro-updated"
    textobject_field = "introduction"


@method_decorator(require_POST, name="dispatch")
class AntiquarianDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = Antiquarian
    permission_required = ("research.delete_antiquarian",)
    success_url = reverse_lazy("antiquarian:list")


class AntiquarianWorksUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = Antiquarian
    form_class = AntiquarianUpdateWorksForm
    permission_required = ("research.change_antiquarian",)
    template_name = "research/antiquarian_works_form.html"

    def get_success_url(self, *args, **kwargs):
        return reverse("antiquarian:detail", kwargs={"pk": self.object.pk})


class AntiquarianWorkCreateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    # the view attribute that needs to be checked for a lock
    check_lock_object = "antiquarian"

    model = Work
    form_class = WorkForm
    permission_required = (
        "research.change_antiquarian",
        "research.add_work",
    )

    def get_success_url(self, *args, **kwargs):
        return reverse("antiquarian:detail", kwargs={"pk": self.antiquarian.pk})

    def dispatch(self, *args, **kwargs):
        # need to ensure the lock-checked attribute is initialised in dispatch
        self.get_antiquarian()
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        work = form.save()
        self.antiquarian.works.add(work)
        return super().form_valid(form)

    def get_antiquarian(self, *args, **kwargs):
        if not getattr(self, "antiquarian", False):
            self.antiquarian = get_object_or_404(Antiquarian, pk=self.kwargs.get("pk"))
        return self.antiquarian

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "antiquarian": self.antiquarian,
            }
        )
        return context


class AntiquarianConcordanceCreateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    check_lock_object = "antiquarian"

    # create a concordance for an original text
    model = AntiquarianConcordance
    permission_required = ("research.add_antiquarianconcordance",)
    fields = ("source", "identifier")

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_antiquarian()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.antiquarian.get_absolute_url()

    def form_valid(self, form):
        concordance = form.save(commit=False)
        concordance.antiquarian = self.get_antiquarian()
        return super().form_valid(form)

    def get_antiquarian(self, *args, **kwargs):
        if not getattr(self, "antiquarian", False):
            self.antiquarian = get_object_or_404(Antiquarian, pk=self.kwargs.get("pk"))
        return self.antiquarian

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "antiquarian": self.get_antiquarian(),
            }
        )
        return context


class AntiquarianConcordanceUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    check_lock_object = "antiquarian"

    model = AntiquarianConcordance
    permission_required = ("research.change_antiquarianconcordance",)
    fields = ("source", "identifier")

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.antiquarian = self.get_object().antiquarian
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "antiquarian": self.antiquarian,
            }
        )
        return context

    def get_success_url(self, *args, **kwargs):
        return self.object.antiquarian.get_absolute_url()


@method_decorator(require_POST, name="dispatch")
class AntiquarianConcordanceDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    check_lock_object = "antiquarian"

    model = AntiquarianConcordance
    permission_required = ("research.delete_antiquarianconcordance",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.antiquarian = self.get_object().antiquarian
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.antiquarian.get_absolute_url()


@require_GET
@login_required
@permission_required("research.change_antiquarian")
def refresh_bibliography_from_mentions(request, pk):
    """Given the pk of an Antiquarian object, call its
    refresh_bibliography_items_from_mentions method to
    parse DynamicTextFields for mentions of bibliography
    items and link these directly."""
    try:
        antiquarian = Antiquarian.objects.get(pk=pk)
    except Antiquarian.DoesNotExist:
        raise Http404("No Antiquarians found matching the query")

    antiquarian.refresh_bibliography_items_from_mentions()

    response = HttpResponse(
        status=204,
    )
    response.headers["HX-Trigger"] = "refreshed-bibliography"
    return response
