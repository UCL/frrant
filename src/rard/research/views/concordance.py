from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import Concordance, Fragment, OriginalText
from rard.research.models.base import FragmentLink
from rard.research.views.mixins import CheckLockMixin


class ConcordanceListView(
        LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'research/concordance_list.html'
    paginate_by = 10
    model = FragmentLink
    permission_required = ('research.view_concordance',)

    def get_queryset(self, *args, **kwargs):
        # just fragments who have original texts that have concordances
        return FragmentLink.objects.filter(
            fragment__original_texts__concordance__isnull=False
        ).distinct()

    def get_context_data(self, *args, object_list=None, **kwargs):
        queryset = self.object_list
        context = super().get_context_data(*args, **kwargs)
        items = [len(o.get_concordance_identifiers()) for o in queryset.all()]
        max_length = max(items) if items else 0
        # supply the max number of columms for the table (for formatting)
        context.update({
            'column_range': range(0, max_length)
        })
        return context


class ConcordanceCreateView(CheckLockMixin, LoginRequiredMixin,
                            PermissionRequiredMixin, CreateView):

    check_lock_object = 'top_level_object'

    # create a concordance for an original text
    model = Concordance
    permission_required = ('research.add_concordance',)
    fields = ('source', 'identifier')

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_original_text().owner
        if not isinstance(self.get_original_text().owner, Fragment):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()

    def form_valid(self, form):
        self.original_text = self.get_original_text()
        concordance = form.save(commit=False)
        concordance.original_text = self.original_text
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


class ConcordanceUpdateView(CheckLockMixin, LoginRequiredMixin,
                            PermissionRequiredMixin, UpdateView):

    check_lock_object = 'top_level_object'

    model = Concordance
    permission_required = ('research.change_concordance',)
    fields = ('source', 'identifier')

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'original_text': self.object.original_text,
        })
        return context

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()
        # o.owner.get_absolute_url()
        # return reverse('original_text:detail', kwargs={'pk': self.object.pk})


@method_decorator(require_POST, name='dispatch')
class ConcordanceDeleteView(CheckLockMixin, LoginRequiredMixin,
                            PermissionRequiredMixin, DeleteView):
    check_lock_object = 'top_level_object'

    model = Concordance
    permission_required = ('research.delete_concordance',)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()
