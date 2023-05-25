from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import (
    TestimoniumAntiquariansForm,
    TestimoniumCommentaryForm,
    TestimoniumForm,
    TestimoniumLinkWorkForm,
)
from rard.research.models import Testimonium
from rard.research.models.base import TestimoniumLink
from rard.research.views.fragment import HistoricalBaseCreateView
from rard.research.views.mixins import (
    CanLockMixin,
    CheckLockMixin,
    GetWorkLinkRequestDataMixin,
)
from rard.utils.shared_functions import reassign_to_unknown


class TestimoniumCreateView(PermissionRequiredMixin, HistoricalBaseCreateView):
    form_class = TestimoniumForm
    success_url_name = "testimonium:detail"
    add_links_url_name = "testimonium:add_work_link"
    title = "Create Testimonium"
    permission_required = ("research.add_testimonium",)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({"title": self.title})
        return context


class TestimoniumListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Testimonium
    permission_required = ("research.view_testimonium",)


class TestimoniumDetailView(
    CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = Testimonium
    permission_required = ("research.view_testimonium",)

    def get_context_data(self, **kwargs):
        testimonium = self.get_object()
        context = super().get_context_data(**kwargs)
        context["inline_update_url"] = "testimonium:update_testimonium_link"

        context["organised_links"] = testimonium.get_organised_links()

        return context


@method_decorator(require_POST, name="dispatch")
class TestimoniumDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = Testimonium
    success_url = reverse_lazy("testimonium:list")
    permission_required = ("research.delete_testimonium",)


class TestimoniumUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = Testimonium
    form_class = TestimoniumForm
    permission_required = ("research.change_testimonium",)

    def get_success_url(self, *args, **kwargs):
        return reverse("testimonium:detail", kwargs={"pk": self.object.pk})


class TestimoniumUpdateAntiquariansView(TestimoniumUpdateView):
    model = Testimonium
    form_class = TestimoniumAntiquariansForm
    permission_required = ("research.change_testimonium",)
    template_name = "research/testimonium_antiquarians_form.html"


class TestimoniumUpdateCommentaryView(TestimoniumUpdateView):
    model = Testimonium
    form_class = TestimoniumCommentaryForm
    permission_required = ("research.change_testimonium",)
    template_name = "research/testimonium_detail.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "editing": "commentary",
            }
        )
        return context


class TestimoniumAddWorkLinkView(
    CheckLockMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GetWorkLinkRequestDataMixin,
    FormView,
):
    check_lock_object = "testimonium"
    is_update = False

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_testimonium()
        return super().dispatch(request, *args, **kwargs)

    template_name = "research/add_work_link.html"
    form_class = TestimoniumLinkWorkForm
    permission_required = (
        "research.change_testimonium",
        "research.add_testimoniumlink",
    )

    def get_success_url(self, *args, **kwargs):
        if "another" in self.request.POST:
            return self.request.path

        return reverse("testimonium:detail", kwargs={"pk": self.get_testimonium().pk})

    def get_testimonium(self, *args, **kwargs):
        if not getattr(self, "testimonium", False):
            self.testimonium = get_object_or_404(Testimonium, pk=self.kwargs.get("pk"))
        return self.testimonium

    def form_valid(self, form):
        data = form.cleaned_data
        antiquarian = data["antiquarian"]

        data["testimonium"] = self.get_testimonium()
        data["antiquarian"] = antiquarian
        TestimoniumLink.objects.get_or_create(**data)

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "testimonium": self.get_testimonium(),
                "work": self.get_work(),
                "antiquarian": self.get_antiquarian(),
            }
        )
        return context

    def get_form_kwargs(self):
        values = super().get_form_kwargs()
        values["antiquarian"] = self.get_antiquarian()
        values["work"] = self.get_work()
        return values


class TestimoniumUpdateWorkLinkView(
    CheckLockMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GetWorkLinkRequestDataMixin,
    UpdateView,
):
    check_lock_object = "testimonium"
    model = TestimoniumLink
    template_name = "research/partials/render_inline_worklink_form.html"
    form_class = TestimoniumLinkWorkForm
    is_update = True
    permission_required = "research.change_testimonium"

    def get_testimonium(self, *args, **kwargs):
        if not getattr(self, "testimonium", False):
            self.testimonium = self.get_object().testimonium
        return self.testimonium

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_testimonium()
        self.get_initial()
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["work"] = self.get_object().work
        initial["antiquarian"] = self.get_object().antiquarian
        initial["book"] = self.get_object().book
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        self.object = self.get_object()

        self.object.definite_antiquarian = data["definite_antiquarian"]
        self.object.definite_work = data["definite_work"]
        self.object.definite_book = data["definite_book"]
        self.object.book = data["book"]

        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "link": self.object,
                "inline_update_url": "testimonium:update_testimonium_link",
                "definite_antiquarian": self.get_definite_antiquarian(),
                "work": self.get_work(),
                "definite_work": self.get_definite_work(),
                "can_edit": True,
                "has_object_lock": True,
            }
        )
        return context

    def get_success_url(self, *args, **kwargs):
        return self.request.META.get(
            "HTTP_REFERER",
            reverse("testimoinum:detail", kwargs={"pk": self.testimonium.pk}),
        )

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        self.object.save()
        context = self.get_context_data()

        return render(request, "research/partials/linked_work.html", context)


@method_decorator(require_POST, name="dispatch")
class RemoveTestimoniumLinkView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    check_lock_object = "testimonium"
    model = TestimoniumLink

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_testimonium()
        return super().dispatch(request, *args, **kwargs)

    permission_required = ("research.change_testimonium",)

    def get_success_url(self, *args, **kwargs):
        return self.request.META.get(
            "HTTP_REFERER",
            reverse("testimonium:detail", kwargs={"pk": self.testimonium.pk}),
        )

    def get_testimonium(self, *args, **kwargs):
        if not getattr(self, "testimonium", False):
            self.testimonium = self.get_object().testimonium
        return self.testimonium

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Determine if it should reassign to unknown
        # if no other links reassign to unknown
        # otherwise delete the link
        antiquarian = self.object.antiquarian
        testimonium = self.get_testimonium()
        if (
            len(
                TestimoniumLink.objects.filter(
                    antiquarian=antiquarian, testimonium=testimonium
                )
            )
            == 1
        ):
            reassign_to_unknown(self)
        else:
            self.object.delete()

        return HttpResponseRedirect(success_url)
