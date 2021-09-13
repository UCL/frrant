from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http.response import Http404
from django.shortcuts import get_object_or_404
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
from rard.research.models import Antiquarian, Testimonium, Work
from rard.research.models.base import TestimoniumLink
from rard.research.views.fragment import HistoricalBaseCreateView
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


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
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, FormView
):

    check_lock_object = "testimonium"

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

    def get_antiquarian(self, *args, **kwargs):
        # look for antiquarian in the GET or POST parameters
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

    def get_work(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.work = None
        if self.request.method == "GET":
            work_pk = self.request.GET.get("work", None)
        elif self.request.method == "POST":
            work_pk = self.request.POST.get("work", None)
        print("work_pk is %s of type %s" % (work_pk, type(work_pk)))
        if work_pk not in ("", None):
            try:
                self.work = Work.objects.get(pk=work_pk)
            except Work.DoesNotExist:
                raise Http404
        return self.work

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
