# from django.contrib.postgres.search import SearchQuery, SearchRank, \
#     SearchVector
from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView

from rard.research.models import (Antiquarian, Fragment, Testimonium, Topic,
                                  Work)


class SearchView(LoginRequiredMixin, TemplateView, ListView):

    paginate_by = 10
    template_name = 'research/search_results.html'
    context_object_name = 'results'

    @property
    def SEARCH_METHODS(self):
        return {
            'antiquarians': self.antiquarian_search,
            'testimonia': self.testimonium_search,
            'fragments': self.fragment_search,
            'topics': self.topic_search,
            'works': self.work_search,
        }

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, keywords):
        qs = Antiquarian.objects.all()
        results = (
            qs.filter(name__icontains=keywords) |
            qs.filter(biography__content__icontains=keywords) |
            qs.filter(re_code__icontains=keywords)
        )
        return results

    @classmethod
    def topic_search(cls, keywords):
        qs = Topic.objects.all()
        results = (
            qs.filter(name__icontains=keywords)
        )
        return results

    @classmethod
    def work_search(cls, keywords):
        qs = Work.objects.all()
        results = (
            qs.filter(name__icontains=keywords) |
            qs.filter(subtitle__icontains=keywords)
        )
        return results

    @classmethod
    def fragment_search(cls, keywords):
        qs = Fragment.objects.all()
        results = (
            qs.filter(original_texts__content__icontains=keywords) |
            qs.filter(original_texts__reference__icontains=keywords) |
            qs.filter(original_texts__translation__translated_text__icontains=keywords) |  # noqa
            qs.filter(original_texts__translation__translator_name__icontains=keywords) |  # noqa
            qs.filter(commentary__content__icontains=keywords)
        )
        return results

    @classmethod
    def testimonium_search(cls, keywords):
        qs = Testimonium.objects.all()
        results = (
            qs.filter(original_texts__content__icontains=keywords) |
            qs.filter(original_texts__reference__icontains=keywords) |
            qs.filter(original_texts__translation__translated_text__icontains=keywords) |  # noqa
            qs.filter(original_texts__translation__translator_name__icontains=keywords) |  # noqa
            qs.filter(commentary__content__icontains=keywords)
        )
        return results

    def get_context_data(self, *args, **kwargs):
        queryset = kwargs.pop('object_list', None)
        if queryset is None:
            self.object_list = self.get_queryset()
        context = super().get_context_data(*args, **kwargs)
        keywords = self.request.GET.get('q')
        to_search = self.request.GET.getlist('what')

        context['search_term'] = keywords
        context['to_search'] = to_search
        context['search_classes'] = self.SEARCH_METHODS.keys()

        return context

    def get_queryset(self):

        keywords = self.request.GET.get('q')
        if not keywords:
            return []

        result_set = []

        to_search = self.request.GET.getlist('what')
        if to_search == ['all']:
            to_search = self.SEARCH_METHODS.keys()

        for what in to_search:
            result_set.append(self.SEARCH_METHODS[what](keywords))

        queryset_chain = chain(*result_set)

        # return a list...
        return sorted(
            queryset_chain,
            key=lambda instance: instance.pk,
            reverse=True
        )
