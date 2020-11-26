from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeleteView

from rard.research.forms import OriginalTextForm
from rard.research.models import Fragment, OriginalText, Testimonium
from rard.research.views.fragment import OriginalTextCitingWorkView
from rard.research.views.mixins import CheckLockMixin


class OriginalTextCreateViewBase(PermissionRequiredMixin,
                                 OriginalTextCitingWorkView):

    template_name = 'research/originaltext_form.html'
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

    def forms_valid(self, forms):
        # save the objects here
        original_text = forms['original_text'].save(commit=False)
        original_text.owner = self.get_parent_object()

        create_citing_work = 'new_citing_work' in self.request.POST

        if create_citing_work:
            original_text.citing_work = forms['new_citing_work'].save()

        original_text.save()

        return super().forms_valid(forms)


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


class OriginalTextUpdateView(CheckLockMixin, SingleObjectMixin,
                             OriginalTextCitingWorkView):

    model = OriginalText
    form_class = OriginalTextForm
    permission_required = ('research.change_originaltext',)
    template_name = 'research/originaltext_form.html'

    check_lock_object = 'parent_object'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.object = self.get_object()
        self.parent_object = self.object.owner
        return super().dispatch(request, *args, **kwargs)

    def get_forms(self):
        forms = super().get_forms()
        # we need to set the instance as we are editing an object
        forms['original_text'] = OriginalTextForm(
            instance=self.object, data=self.request.POST or None
        )
        return forms

    def get_success_url(self, *args, **kwargs):
        return self.object.owner.get_absolute_url()

    def forms_valid(self, forms):
        # save the objects here
        original_text = forms['original_text'].save(commit=False)
        original_text.owner = self.object.owner

        create_citing_work = 'new_citing_work' in self.request.POST

        if create_citing_work:
            original_text.citing_work = forms['new_citing_work'].save()

        original_text.save()

        return super().forms_valid(forms)


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
