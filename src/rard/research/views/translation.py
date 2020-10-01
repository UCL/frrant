from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import OriginalText, Translation


class TranslationCreateView(LoginRequiredMixin, CreateView):
    model = Translation
    fields = ['translated_text', 'translator_name', 'approved']

    def get_success_url(self, *args, **kwargs):
        return self.get_original_text().owner.get_absolute_url()

    def form_valid(self, form):
        translation = form.save(commit=False)
        translation.original_text = self.get_original_text()
        translation.save()
        return super().form_valid(form)

    def get_original_text(self, *args, **kwargs):
        if not getattr(self, 'original_text', False):
            self.original_text = get_object_or_404(
                OriginalText,
                pk=self.kwargs.get('pk')
            )
        return self.original_text

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'original_text': self.get_original_text(),
        })
        return context


class TranslationUpdateView(LoginRequiredMixin, UpdateView):
    model = Translation
    fields = ['translated_text', 'translator_name', 'approved']

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'original_text': self.object.original_text,
        })
        return context


@method_decorator(require_POST, name='dispatch')
class TranslationDeleteView(LoginRequiredMixin, DeleteView):
    model = Translation

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()
