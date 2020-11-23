from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import BookForm
from rard.research.models import Book, CitingWork
from rard.research.views.mixins import (CanLockMixin, CheckLockMixin,
                                        DateOrderMixin)


class CitingWorkListView(DateOrderMixin, LoginRequiredMixin,
                         PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = CitingWork
    permission_required = ('research.view_citingwork',)


class CitingWorkDetailView(CanLockMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, DetailView):
    model = CitingWork
    permission_required = ('research.view_citingwork',)


class CitingWorkUpdateView(CheckLockMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, UpdateView):
    model = CitingWork
    fields = ('author', 'title', 'edition',)
    permission_required = ('research.change_citingwork',)

    def get_success_url(self, *args, **kwargs):
        return reverse('citingwork:detail', kwargs={'pk': self.object.pk})


@method_decorator(require_POST, name='dispatch')
class CitingWorkDeleteView(CheckLockMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, DeleteView):
    model = CitingWork
    success_url = reverse_lazy('citingwork:list')
    permission_required = ('research.delete_citingwork',)
