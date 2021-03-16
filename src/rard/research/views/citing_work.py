from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import CitingAuthor, CitingWork
from rard.research.views.mixins import (CanLockMixin, CheckLockMixin,
                                        DateOrderMixin)


class CitingAuthorCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                             CreateView):
    model = CitingAuthor
    permission_required = ('research.add_citingauthor',)
    fields = ('name', 'order_name', 'order_year', 'date_range',)

    def get_success_url(self, *args, **kwargs):
        return reverse('citingauthor:detail', kwargs={'pk': self.object.pk})


class CitingAuthorUpdateView(CheckLockMixin, LoginRequiredMixin,
                             PermissionRequiredMixin, UpdateView):
    model = CitingAuthor
    fields = ('name', 'order_name', 'order_year', 'date_range',)
    permission_required = ('research.change_citingauthor',)

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'citingauthor:detail', kwargs={'pk': self.object.pk}
        )


class CitingAuthorListView(DateOrderMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = CitingAuthor
    permission_required = (
        'research.view_citingauthor', 'research.view_citingwork',
    )


class CitingAuthorDetailView(CanLockMixin, LoginRequiredMixin,
                             PermissionRequiredMixin, DetailView):
    model = CitingAuthor
    permission_required = ('research.view_citingauthor',)


@method_decorator(require_POST, name='dispatch')
class CitingAuthorDeleteView(CheckLockMixin, LoginRequiredMixin,
                             PermissionRequiredMixin, DeleteView):
    model = CitingAuthor
    success_url = reverse_lazy('citingauthor:list')
    permission_required = ('research.delete_citingauthor',)


class CitingWorkDetailView(CanLockMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, DetailView):
    model = CitingWork
    permission_required = ('research.view_citingwork',)


class CitingWorkUpdateView(CheckLockMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, UpdateView):
    model = CitingWork
    fields = ('author', 'title', 'edition', 'order_year', 'date_range',)

    permission_required = ('research.change_citingwork',)

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'citingauthor:work_detail', kwargs={'pk': self.object.pk}
        )


@method_decorator(require_POST, name='dispatch')
class CitingWorkDeleteView(CheckLockMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, DeleteView):
    model = CitingWork
    success_url = reverse_lazy('citingauthor:list')
    permission_required = ('research.delete_citingwork',)
