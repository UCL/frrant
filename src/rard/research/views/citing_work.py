from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import CitingWorkCreateForm
from rard.research.models import CitingAuthor, CitingWork
from rard.research.views.mixins import (CanLockMixin, CheckLockMixin,
                                        DateOrderMixin)


class CitingAuthorCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                             CreateView):
    model = CitingAuthor
    permission_required = ('research.add_citingauthor',)
    fields = ('name', 'order_name', 'order_year', 'date_range',)

    def get_success_url(self, *args, **kwargs):
        if 'then_add_works' in self.request.POST:
            return reverse(
                'citingauthor:create_work_for_author',
                kwargs={
                    'pk': self.object.pk
                }
            )
        return reverse('citingauthor:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        ret = super().form_valid(form)
        if 'then_add_works' in self.request.POST:
            # lock the object
            self.object.lock(self.request.user)
        return ret


class CitingAuthorUpdateView(CheckLockMixin, LoginRequiredMixin,
                             PermissionRequiredMixin, UpdateView):
    model = CitingAuthor
    fields = ('name', 'order_name', 'order_year', 'date_range',)
    permission_required = ('research.change_citingauthor',)

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'citingauthor:detail', kwargs={'pk': self.object.pk}
        )


from rard.research.models import OriginalText
class CitingAuthorListView(DateOrderMixin, LoginRequiredMixin,
                           PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = OriginalText
    template_name = 'research/citingauthor_list.html'
    permission_required = (
        'research.view_citingauthor', 'research.view_citingwork',
    )
    def get_queryset(self):
        # NB do not call super() method here as we are doing something
        # differnt with the date ordering here
        ordering = ['citing_work__author']
        if self.request.GET.get('order') == 'earliest':
            ordering = ['citing_work__author__order_year', 'citing_work__author']
        elif self.request.GET.get('order') == 'latest':
            ordering = ['-citing_work__author__order_year', '-citing_work__author']            

        ordering += [
            'content_type',  # by fragment, then testimonium, then anon frag
            'citing_work',   # group by work
            'reference_order'  # then by reference
        ]
        return OriginalText.objects.all().order_by(*ordering)


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


class CitingAuthorCreateWorkView(LoginRequiredMixin, PermissionRequiredMixin,
                                 CreateView):
    # creates a work specifically for a named citing author
    model = CitingWork
    permission_required = (
        'research.add_citingwork', 'research.change_citingauthor',
    )
    form_class = CitingWorkCreateForm

    def dispatch(self, *args, **kwargs):
        self.get_citing_author()
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        work = form.save(commit=False)
        work.author = self.citing_author
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial['author'] = self.citing_author
        return initial

    def get_citing_author(self, *args, **kwargs):
        if not getattr(self, 'citing_author', False):
            self.citing_author = get_object_or_404(
                CitingAuthor,
                pk=self.kwargs.get('pk')
            )
        return self.citing_author

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'citing_author': self.citing_author,
        })
        return context

    def get_success_url(self, *args, **kwargs):
        if 'another' in self.request.POST:
            return self.request.path
        return reverse(
            'citingauthor:work_detail', kwargs={'pk': self.object.pk}
        )


class CitingWorkCreateView(LoginRequiredMixin, PermissionRequiredMixin,
                           CreateView):
    model = CitingWork
    permission_required = ('research.add_citingwork',)
    form_class = CitingWorkCreateForm

    def get_success_url(self, *args, **kwargs):
        if 'another' in self.request.POST:
            return self.request.path
        return reverse(
            'citingauthor:work_detail', kwargs={'pk': self.object.pk}
        )


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
