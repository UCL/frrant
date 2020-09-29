from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import OriginalTextForm
from rard.research.models import Fragment, OriginalText, Testimonium


class OriginalTextCreateViewBase(LoginRequiredMixin, CreateView):
    model = OriginalText
    form_class = OriginalTextForm

    def get_success_url(self, *args, **kwargs):
        return self.get_parent_object().get_detail_url()

    def get_parent_object(self, *args, **kwargs):
        if not getattr(self, 'parent_object', False):
            self.parent_object = get_object_or_404(
                self.parent_object_class,
                pk=self.kwargs.get('pk')
            )
        return self.parent_object

    def form_valid(self, form):
        original_text = form.save(commit=False)
        original_text.owner = self.get_parent_object()
        original_text.save()
        return super().form_valid(form)


class FragmentOriginalTextCreateView(OriginalTextCreateViewBase):
    parent_object_class = Fragment


class TestimoniumOriginalTextCreateView(OriginalTextCreateViewBase):
    parent_object_class = Testimonium


class OriginalTextUpdateView(LoginRequiredMixin, UpdateView):
    model = OriginalText
    form_class = OriginalTextForm

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_detail_url()


@method_decorator(require_POST, name='dispatch')
class OriginalTextDeleteView(LoginRequiredMixin, DeleteView):
    model = OriginalText

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_detail_url()
