from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import Topic


class TopicListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Topic


class TopicDetailView(LoginRequiredMixin, DetailView):
    model = Topic


class TopicCreateView(LoginRequiredMixin, CreateView):
    model = Topic
    fields = ('name',)

    def get_success_url(self, *args, **kwargs):
        return reverse('topic:list')


class TopicUpdateView(LoginRequiredMixin, UpdateView):
    model = Topic
    fields = ('name',)

    def get_success_url(self, *args, **kwargs):
        return reverse('topic:detail', kwargs={'slug': self.object.slug})


class TopicDeleteView(LoginRequiredMixin, DeleteView):
    model = Topic
    success_url = reverse_lazy('topic:list')
