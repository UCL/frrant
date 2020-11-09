from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import OriginalTextForm
from rard.research.models import Fragment, OriginalText, Testimonium
from rard.research.views.mixins import CheckLockMixin


class OriginalTextCreateViewBase(CheckLockMixin, LoginRequiredMixin,
                                 PermissionRequiredMixin, CreateView):

    check_lock_object = 'parent_object'

    model = OriginalText
    form_class = OriginalTextForm

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_parent_object()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.get_parent_object().get_absolute_url()

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
    permission_required = (
        'research.add_originaltext', 'research.change_fragment',
    )


class TestimoniumOriginalTextCreateView(OriginalTextCreateViewBase):
    parent_object_class = Testimonium
    permission_required = (
        'research.add_originaltext', 'research.change_testimonium',
    )


class OriginalTextUpdateView(CheckLockMixin, LoginRequiredMixin, UpdateView):
    model = OriginalText
    form_class = OriginalTextForm
    permission_required = ('research.change_originaltext',)

    check_lock_object = 'parent_object'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.parent_object = self.get_object().owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_absolute_url()


@method_decorator(require_POST, name='dispatch')
class OriginalTextDeleteView(CheckLockMixin, LoginRequiredMixin, DeleteView):

    check_lock_object = 'parent_object'

    model = OriginalText
    permission_required = ('research.delete_originaltext',)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.parent_object = self.get_object().owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_absolute_url()
