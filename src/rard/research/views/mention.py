# from django.contrib.postgres.search import SearchQuery, SearchRank, \
#     SearchVector
from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import View

from rard.research.models import (AnonymousFragment, Antiquarian, Fragment,
                                  Testimonium, Topic, Work)


@method_decorator(require_GET, name='dispatch')
class MentionSearchView(LoginRequiredMixin, View):

    context_object_name = 'results'

    @property
    def SEARCH_METHODS(self):
        return {
            'antiquarians': self.antiquarian_search,
            'testimonia': self.testimonium_search,
            'anonymous fragments': self.anonymous_fragment_search,
            'fragments': self.fragment_search,
            'topics': self.topic_search,
            'works': self.work_search,
        }

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, keywords):
        qs = Antiquarian.objects.all()
        results = (
            qs.filter(name__icontains=keywords)
        )
        return results.distinct()

    @classmethod
    def topic_search(cls, keywords):
        qs = Topic.objects.all()
        results = (
            qs.filter(name__icontains=keywords)
        )
        return results.distinct()

    @classmethod
    def work_search(cls, keywords):
        qs = Work.objects.all()
        results = (
            qs.filter(name__icontains=keywords)
        )
        return results.distinct()

    @classmethod
    def fragment_search(cls, keywords):
        qs = Fragment.objects.all()
        results = (
            qs.filter(
                antiquarian_fragmentlinks__antiquarian__name__icontains=keywords  # noqa
            )
        )
        return results.distinct()

    @classmethod
    def remove_keyword(cls, kw, keywords):
        if not keywords or not keywords[0].lower().startswith(kw):
            return None
        k = keywords[0][len(kw):]
        if len(k) == 0:
            return keywords[1:]
        keywords[0] = k
        return keywords

    @classmethod
    def anonymous_fragment_search(cls, keywords):
        qs = AnonymousFragment.objects.all()
        kws = keywords.split()
        ids = cls.remove_keyword('f', kws)
        if ids == None or 1 < len(ids):
            return qs.none()
        if len(ids) == 0:
            return qs
        if not ids[0].isnumeric():
            return qs.none()
        return qs.filter(order=int(ids[0])-1)

    @classmethod
    def testimonium_search(cls, keywords):
        qs = Testimonium.objects.all()
        results = (
            qs.filter(
                antiquarian_testimoniumlinks__antiquarian__name__icontains=keywords  # noqa
            )
        )
        return results.distinct()

    def get(self, request, *args, **kwargs):

        if not request.is_ajax():
            raise Http404

        ajax_data = []

        from django.apps import apps
        dd = apps.all_models['research']
        model_name_cache = {}

        # return just the name, pk and type for display
        for o in self.get_queryset():
            model_name = model_name_cache.get(o.__class__, None)
            if not model_name:
                model_name = next(
                    k for k, value in dd.items() if value == o.__class__)
                model_name_cache[o.__class__] = model_name

            ajax_data.append(
                {
                    'id': o.pk,
                    'target': model_name,
                    'value': str(o)
                }
            )

        return JsonResponse(data=ajax_data, safe=False)

    def get_queryset(self):
        keywords = self.request.GET.get('q')
        if not keywords:
            return []

        result_set = []
        to_search = self.SEARCH_METHODS.keys()
        for what in to_search:
            result_set.append(self.SEARCH_METHODS[what](keywords))

        queryset_chain = chain(*result_set)

        # return a of results
        return sorted(
            queryset_chain,
            key=lambda instance: instance.pk,
            reverse=True
        )
