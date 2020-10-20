from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import Work


class WorkListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Work
    permission_required = ('research.view_work',)


class WorkDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Work
    permission_required = ('research.view_work',)


class WorkCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Work
    fields = '__all__'
    success_url = reverse_lazy('work:list')
    permission_required = ('research.add_work',)


class WorkUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Work
    fields = '__all__'
    permission_required = ('research.change_work',)

    def get_success_url(self, *args, **kwargs):
        return reverse('work:detail', kwargs={'pk': self.object.pk})


@method_decorator(require_POST, name='dispatch')
class WorkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Work
    success_url = reverse_lazy('work:list')
    permission_required = ('research.delete_work',)
