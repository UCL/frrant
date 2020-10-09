from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import Concordance, OriginalText


class ConcordanceListView(
        LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Concordance
    permission_required = ('research.view_concordance',)


class ConcordanceCreateView(
        LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # create a concordance for an original text
    model = Concordance
    permission_required = ('research.add_concordance',)
    fields = ('source', 'identifier')

    # success_url = reverse_lazy('concordance:list')
    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()

    def form_valid(self, form):
        self.original_text = self.get_original_text()
        concordance = form.save(commit=False)
        concordance.original_text = self.original_text
        concordance.save()
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


class ConcordanceUpdateView(
        LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Concordance
    permission_required = ('research.change_concordance',)
    fields = ('source', 'identifier')
    # success_url = reverse_lazy('concordance:list')

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
class ConcordanceDeleteView(
        LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Concordance
    permission_required = ('research.delete_concordance',)

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()
