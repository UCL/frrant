from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import Topic
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class TopicListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Topic
    permission_required = ('research.view_topic',)


class TopicDetailView(CanLockMixin, LoginRequiredMixin,
                      PermissionRequiredMixin, DetailView):
    model = Topic
    permission_required = ('research.view_topic',)


class TopicCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Topic
    fields = ('name',)
    permission_required = ('research.add_topic',)

    def get_success_url(self, *args, **kwargs):
        return reverse('topic:list')


class TopicUpdateView(CheckLockMixin, LoginRequiredMixin,
                      PermissionRequiredMixin, UpdateView):
    model = Topic
    fields = ('name',)
    permission_required = ('research.change_topic',)

    def get_success_url(self, *args, **kwargs):
        return reverse('topic:detail', kwargs={'slug': self.object.slug})


@method_decorator(require_POST, name='dispatch')
class TopicDeleteView(CheckLockMixin, LoginRequiredMixin,
                      PermissionRequiredMixin, DeleteView):
    model = Topic
    success_url = reverse_lazy('topic:list')
    permission_required = ('research.delete_topic',)
