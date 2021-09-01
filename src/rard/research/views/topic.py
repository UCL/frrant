import itertools

from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import Topic
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class TopicListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Topic
    permission_required = ('research.view_topic',)

    def post(self, *args, **kwargs):
        pk = self.request.POST.get('topic_id', None)
        if pk is not None:
            try:
                topic = Topic.objects.get(pk=pk)
                if 'up' in self.request.POST:
                    topic.up()
                elif 'down' in self.request.POST:
                    topic.down()

            except (Topic.DoesNotExist):
                pass
        return HttpResponseRedirect(self.request.path)


class TopicDetailView(CanLockMixin, LoginRequiredMixin,
                      PermissionRequiredMixin, DetailView):
    model = Topic
    permission_required = ('research.view_topic',)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        fragment_qs = self.get_object().fragment_set.all()
        anonymousfragment_qs = self.get_object().anonymousfragment_set.all()
        order = self.request.GET.get('order', None)
        if order == 'citing_author':
            fragment_qs = fragment_qs.order_by(
                'original_texts__citing_work__author__name'
                )
            anonymousfragment_qs = anonymousfragment_qs.order_by(
                'original_texts__citing_work__author__name'
                )
        else:
            fragment_qs = fragment_qs.order_by(
                'antiquarian_fragmentlinks__antiquarian__order_name'
            )
        # Remove duplicates, but preserve order for both querysets
        fragment_qs = list(dict.fromkeys(fragment_qs))
        anonymousfragment_qs = list(dict.fromkeys(anonymousfragment_qs))

        context.update({
            'fragments': fragment_qs,
            'anonymous_fragments': anonymousfragment_qs,
            'order': order,
        })
        return context


class TopicCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Topic
    fields = ('name',)
    permission_required = ('research.add_topic',)

    def get_success_url(self, *args, **kwargs):
        if 'another' in self.request.POST:
            return self.request.path
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


class MoveTopicView(LoginRequiredMixin, View):

    render_partial_template = 'research/partials/ordered_topic_area.html'

    def render_valid_response(self, page_index):
        from django.core.paginator import Paginator
        view = TopicListView()
        pages = Paginator(view.get_queryset(), view.paginate_by)
        context = {
            'page_obj': pages.page(page_index),
            'has_object_lock': True,
            'can_edit': True,
            'perms': PermWrapper(self.request.user)
        }
        html = render_to_string(self.render_partial_template, context)
        ajax_data = {'status': 200, 'html': html}
        return JsonResponse(data=ajax_data, safe=False)

    def post(self, *args, **kwargs):

        topic_pk = self.request.POST.get('topic_id', None)
        page_index = self.request.POST.get('page_index', None)
        if topic_pk:
            # moving a topic in the collection
            try:
                topic = Topic.objects.get(pk=topic_pk)

                if 'move_to' in self.request.POST:
                    pos = int(self.request.POST.get('move_to'))
                    topic.move_to(pos)

                return self.render_valid_response(int(page_index))

            except (Topic.DoesNotExist, KeyError):
                raise Http404

        raise Http404
