from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import resolve, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import (
    OriginalTextAuthorForm,
    OriginalTextDetailsForm,
    OriginalTextForm,
)
from rard.research.models import (
    AnonymousFragment,
    CitingAuthor,
    CitingWork,
    Fragment,
    OriginalText,
    Testimonium,
)
from rard.research.views.fragment import OriginalTextCitingWorkView
from rard.research.views.mixins import CheckLockMixin


class OriginalTextCreateViewBase(PermissionRequiredMixin, OriginalTextCitingWorkView):

    template_name = "research/originaltext_form.html"
    check_lock_object = "parent_object"

    model = OriginalText
    form_class = OriginalTextForm

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_parent_object()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        if "then_add_apparatus_criticus" in self.request.POST:
            # load the update view for the original text
            # (but needs to be in the correct namespace for the parent)
            namespace = resolve(self.request.path_info).namespace
            return reverse(
                "%s:update_original_text" % namespace,
                kwargs={"pk": self.original_text.pk},
            )
        return self.get_parent_object().get_absolute_url()

    def get_parent_object(self, *args, **kwargs):
        if not getattr(self, "parent_object", False):
            self.parent_object = get_object_or_404(
                self.parent_object_class, pk=self.kwargs.get("pk")
            )
        return self.parent_object

    def forms_valid(self, forms):
        # save the objects here

        self.original_text = forms["original_text"].save(commit=False)
        self.original_text.owner = self.get_parent_object()

        create_citing_work = "new_citing_work" in self.request.POST

        if create_citing_work:
            self.original_text.citing_work = forms["new_citing_work"].save()

        self.original_text.save()

        return super().forms_valid(forms)


class FragmentOriginalTextCreateView(OriginalTextCreateViewBase):
    parent_object_class = Fragment
    permission_required = (
        "research.add_originaltext",
        "research.change_fragment",
    )


class AnonymousFragmentOriginalTextCreateView(OriginalTextCreateViewBase):
    parent_object_class = AnonymousFragment
    permission_required = (
        "research.add_originaltext",
        "research.change_fragment",
    )


class TestimoniumOriginalTextCreateView(OriginalTextCreateViewBase):
    parent_object_class = Testimonium
    permission_required = (
        "research.add_originaltext",
        "research.change_testimonium",
    )


class OriginalTextUpdateAuthorView(CheckLockMixin, UpdateView):
    model = OriginalText
    form_class = OriginalTextAuthorForm
    permission_required = ("research.change_originaltext",)
    template_name = "research/originaltext_author_form.html"
    check_lock_object = "parent_object"

    def get_citing_author_from_form(self, *args, **kwargs):
        # look for author in the GET or POST parameters
        self.citing_author = None
        if self.request.method == "GET":
            author_pk = self.request.GET.get("citing_author", None)
        elif self.request.method == "POST":
            author_pk = self.request.POST.get("citing_author", None)
        if author_pk:
            try:
                self.citing_author = CitingAuthor.objects.get(pk=author_pk)
            except CitingAuthor.DoesNotExist:
                raise Http404
        return self.citing_author

    def get_citing_work_from_form(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.citing_work = None
        if self.request.method == "GET":
            author_pk = self.request.GET.get("citing_work", None)
        elif self.request.method == "POST":
            author_pk = self.request.POST.get("citing_work", None)
        if author_pk:
            try:
                self.citing_work = CitingWork.objects.get(pk=author_pk)
            except CitingWork.DoesNotExist:
                raise Http404
        return self.citing_work

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.object = self.get_object()
        self.parent_object = self.object.owner
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        form_author = self.get_citing_author_from_form()

        context.update(
            {
                "citing_author": form_author or self.object.citing_work.author,
                "citing_work": self.get_citing_work_from_form()
                or self.object.citing_work,
            }
        )
        if form_author:
            # insist that we also use the selected citing work value
            context["citing_work"] = self.get_citing_work_from_form()

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["citing_author"] = (
            self.get_citing_author_from_form() or self.object.citing_work.author
        )
        kwargs["citing_work"] = (
            self.get_citing_work_from_form() or self.object.citing_work
        )
        return kwargs

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_absolute_url()


class OriginalTextUpdateView(CheckLockMixin, UpdateView):

    model = OriginalText
    form_class = OriginalTextDetailsForm
    permission_required = ("research.change_originaltext",)
    template_name = "research/originaltext_update_form.html"

    check_lock_object = "parent_object"

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.object = self.get_object()
        self.parent_object = self.object.owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_absolute_url()


@method_decorator(require_POST, name="dispatch")
class OriginalTextDeleteView(CheckLockMixin, LoginRequiredMixin, DeleteView):

    check_lock_object = "parent_object"

    model = OriginalText
    permission_required = ("research.delete_originaltext",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.parent_object = self.get_object().owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_absolute_url()
