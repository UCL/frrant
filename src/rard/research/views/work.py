from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import Work


class WorkListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Work


class WorkDetailView(LoginRequiredMixin, DetailView):
    model = Work


class WorkCreateView(LoginRequiredMixin, CreateView):
    model = Work
    fields = '__all__'
    success_url = reverse_lazy('work:list')


class WorkUpdateView(LoginRequiredMixin, UpdateView):
    model = Work
    fields = '__all__'

    def get_success_url(self, *args, **kwargs):
        return reverse('work:detail', kwargs={'pk': self.object.pk})


@method_decorator(require_POST, name='dispatch')
class WorkDeleteView(LoginRequiredMixin, DeleteView):
    model = Work
    success_url = reverse_lazy('work:list')
