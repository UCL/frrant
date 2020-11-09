from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import BookForm, WorkForm
from rard.research.models import Book, Work
from rard.research.views.mixins import (CanLockMixin, CheckLockMixin,
                                        DateOrderMixin)


class WorkListView(DateOrderMixin, LoginRequiredMixin, PermissionRequiredMixin,
                   ListView):
    paginate_by = 10
    model = Work
    permission_required = ('research.view_work',)


class WorkDetailView(
        CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Work
    permission_required = ('research.view_work',)


class WorkCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Work
    form_class = WorkForm
    success_url = reverse_lazy('work:list')
    permission_required = ('research.add_work',)


class WorkUpdateView(CheckLockMixin, LoginRequiredMixin,
                     PermissionRequiredMixin, UpdateView):
    model = Work
    form_class = WorkForm
    permission_required = ('research.change_work',)

    def get_success_url(self, *args, **kwargs):
        return reverse('work:detail', kwargs={'pk': self.object.pk})


@method_decorator(require_POST, name='dispatch')
class WorkDeleteView(CheckLockMixin, LoginRequiredMixin,
                     PermissionRequiredMixin, DeleteView):
    model = Work
    success_url = reverse_lazy('work:list')
    permission_required = ('research.delete_work',)


class BookCreateView(CheckLockMixin, LoginRequiredMixin,
                     PermissionRequiredMixin, CreateView):
    # the view attribute that needs to be checked for a lock
    check_lock_object = 'work'

    model = Book
    form_class = BookForm
    permission_required = (
        'research.change_work', 'research.add_book',
    )

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_work()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return reverse('work:detail', kwargs={'pk': self.work.pk})

    def get_work(self, *args, **kwargs):
        if not getattr(self, 'work', False):
            self.work = get_object_or_404(
                Work,
                pk=self.kwargs.get('pk')
            )
        return self.work

    def form_valid(self, form):
        book = form.save(commit=False)
        book.work = self.get_work()
        book.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'work': self.get_work(),
        })
        return context


class BookUpdateView(CheckLockMixin, LoginRequiredMixin,
                     PermissionRequiredMixin, UpdateView):

    # the view attribute that needs to be checked for a lock
    check_lock_object = 'work'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_work()
        return super().dispatch(request, *args, **kwargs)

    def get_work(self, *args, **kwargs):
        if not getattr(self, 'work', False):
            self.work = self.get_object().work
        return self.work

    model = Book
    form_class = BookForm
    permission_required = (
        'research.change_work', 'research.change_book',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse('work:detail', kwargs={'pk': self.object.work.pk})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'work': self.get_work(),
        })
        return context


@method_decorator(require_POST, name='dispatch')
class BookDeleteView(
        LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    permission_required = (
        'research.change_work', 'research.delete_book',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse('work:detail', kwargs={'pk': self.object.work.pk})
