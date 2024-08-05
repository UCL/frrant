from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import OriginalText, Translation
from rard.research.views.mixins import CheckLockMixin


class TranslationCreateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    check_lock_object = "top_level_object"

    model = Translation
    fields = ["translated_text", "translator_name", "approved"]
    permission_required = ("research.add_translation",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_original_text().owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.top_level_object.get_absolute_url()

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["translated_text"].widget.attrs["class"] = "enableCKEditor"
        return form

    def form_valid(self, form):
        translation = form.save(commit=False)
        translation.original_text = self.get_original_text()
        return super().form_valid(form)

    def get_original_text(self, *args, **kwargs):
        if not getattr(self, "original_text", False):
            self.original_text = get_object_or_404(
                OriginalText, pk=self.kwargs.get("pk")
            )
        return self.original_text

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "original_text": self.get_original_text(),
            }
        )
        return context


class TranslationUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    check_lock_object = "top_level_object"

    model = Translation
    fields = ["translated_text", "translator_name", "approved"]
    permission_required = ("research.change_translation",)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["translated_text"].widget.attrs["class"] = "enableCKEditor"
        return form

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.top_level_object.get_absolute_url()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "original_text": self.object.original_text,
            }
        )
        return context


@method_decorator(require_POST, name="dispatch")
class TranslationDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    check_lock_object = "top_level_object"

    model = Translation
    permission_required = ("research.delete_translation",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.top_level_object.get_absolute_url()
