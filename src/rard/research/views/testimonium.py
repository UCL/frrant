from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView, View

from rard.research.forms import (
    TestimoniumAntiquariansForm,
    TestimoniumCommentaryForm,
    TestimoniumForm,
    TestimoniumLinkWorkForm,
    TestimoniumPublicCommentaryForm,
)
from rard.research.models import Antiquarian, Testimonium
from rard.research.models.base import TestimoniumLink
from rard.research.views.fragment import (
    AnonymousFragmentConvertToFragmentView,
    HistoricalBaseCreateView,
)
from rard.research.views.mixins import (
    CanLockMixin,
    CheckLockMixin,
    GetWorkLinkRequestDataMixin,
    TextObjectFieldUpdateMixin,
    TextObjectFieldViewMixin,
)
from rard.utils.convertors import convert_testimonium_to_unlinked_fragment
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


class TestimoniumUpdateCommentaryView(
    TextObjectFieldUpdateMixin, TestimoniumUpdateView
):
    form_class = TestimoniumCommentaryForm
    textobject_field = "commentary"
    template_name = "research/inline_forms/commentary_form.html"
    hide_empty = False


class TestimoniumUpdatePublicCommentaryView(
    TextObjectFieldUpdateMixin, TestimoniumUpdateView
):
    form_class = TestimoniumPublicCommentaryForm
    textobject_field = "public_commentary_mentions"
    template_name = "research/inline_forms/public_commentary_form.html"
    hide_empty = False


class TestimoniumCommentaryView(TextObjectFieldViewMixin):
    model = Testimonium
    permission_required = ("research.view_testimonium",)
    textobject_field = "commentary"
    hide_empty = False


class TestimoniumPublicCommentaryView(TextObjectFieldViewMixin):
    model = Testimonium
    permission_required = ("research.view_testimonium",)
    textobject_field = "public_commentary_mentions"
    hide_empty = False


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
    template_name = "research/inline_forms/render_inline_worklink_form.html"
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
        if "cancel" in self.request.POST:
            return reverse("testimonium:detail", kwargs={"pk": self.testimonium.pk})
        else:
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
            reverse("testimonium:detail", kwargs={"pk": self.testimonium.pk}),
        )

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        self.object.save()
        context = self.get_context_data()

        return render(request, "research/partials/linked_work.html", context)


@method_decorator(require_POST, name="dispatch")
class RemoveTestimoniumLinkView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, View
):
    """
    Just a POST endpoint for deleting a Testimonium link.

    Two modes of operation: if the form has ``antiquarian_request`` then
    this is the PK of the Testimonium and the URL PK is for the Antiquarian;
    in this case all the ``TestimoniumLinks`` between this Antiquarian and
    this Testimonium will be removed.

    If the form has no ``antiquarian_request`` then the URL PK is for the
    ``TestimoniumLink`` and this will be removed.
    """

    check_lock_object = "testimonium"
    model = TestimoniumLink

    permission_required = ("research.change_testimonium",)

    def get_object(self):
        """Get the object that we need to check the lock for: this is the Testimonium."""
        return self.testimonium

    def dispatch(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        antiquarian_request = request.POST.get("antiquarian_request", None)
        if antiquarian_request is None:
            self.link = TestimoniumLink.objects.get(pk=pk)
            self.testimonium = self.link.testimonium
            self.antiquarian = self.link.antiquarian
        else:
            self.link = None
            self.testimonium = Testimonium.objects.get(pk=antiquarian_request)
            self.antiquarian = Antiquarian.objects.get(pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.META.get(
            "HTTP_REFERER",
            reverse("testimonium:detail", kwargs={"pk": self.testimonium.pk}),
        )

    def get_response(self):
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if self.link is None:
            self.model.objects.filter(
                antiquarian=self.antiquarian,
                testimonium=self.testimonium,
            ).delete()
            return self.get_response()
        how_many_links = TestimoniumLink.objects.filter(
            antiquarian=self.antiquarian,
            testimonium=self.testimonium,
        ).count()
        if how_many_links == 1:
            reassign_to_unknown(self.link)
        else:
            self.link.delete()
        return self.get_response()


@method_decorator(require_POST, name="dispatch")
class TestimoniumConvertToUnlinkedFragmentView(AnonymousFragmentConvertToFragmentView):
    model = Testimonium
    permission_required = "research.change_fragment"

    def post(self, request, *args, **kwargs):
        fragment = convert_testimonium_to_unlinked_fragment(self.get_object())
        success_url = reverse("fragment:detail", kwargs={"pk": fragment.pk})
        return HttpResponseRedirect(success_url)
