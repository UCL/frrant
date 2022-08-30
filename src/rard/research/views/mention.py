# from django.contrib.postgres.search import SearchQuery, SearchRank, \
#     SearchVector
from itertools import chain
from unicodedata import numeric

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import View

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    Fragment,
    Testimonium,
    Topic,
    Work,
)


@method_decorator(require_GET, name="dispatch")
class MentionSearchView(LoginRequiredMixin, View):

    context_object_name = "results"

    @property
    def SEARCH_METHODS(self):
        return {
            "aq": self.antiquarian_search,
            "tt": self.testimonium_search,
            "af": self.anonymous_fragment_search,
            "fr": self.fragment_search,
            "tp": self.topic_search,
            "wk": self.work_search,
            "bi": self.bibliography_search,
            "uf": self.unlinked_fragment_search,
        }

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, keywords):
        qs = Antiquarian.objects.all()
        results = qs.filter(name__icontains=keywords)
        return results.distinct()

    @classmethod
    def topic_search(cls, keywords):
        qs = Topic.objects.all()
        results = qs.filter(name__icontains=keywords)
        return results.distinct()

    @classmethod
    def work_search(cls, keywords):
        qs = Work.objects.all()
        results = qs.filter(name__icontains=keywords)
        return results.distinct()

    def order_number_search(keywords):
        order_number = None
        for kw in keywords:
            if kw.isnumeric():
                order_number = int(kw)
                keywords.remove(kw)

        return order_number, keywords

    @classmethod
    def fragment_search(cls, keywords):
        order_number, antiquarian = cls.order_number_search(keywords)
        qs = Fragment.objects.all()
        # if the keyword is a number then use order number search
        if order_number:
            order_number = order_number - 1
            """either the antiquarian order number is the order number or the work order number is the order number"""
            order_query = Q(antiquarian_fragmentlinks__order=order_number) | Q(
                antiquarian_fragmentlinks__work_order=order_number
            )

        else:
            order_query = Q()

        if antiquarian:
            ant_query = Q()
            for a in antiquarian:
                ant_query = ant_query & Q(
                    antiquarian_fragmentlinks__antiquarian__name__icontains=a
                )
        else:
            ant_query = Q()
        results = qs.filter(ant_query, order_query)
        return results.distinct()

    @classmethod
    def remove_keyword(cls, kw, keywords):
        if not keywords or not keywords[0].lower().startswith(kw):
            return None
        k = keywords[0][len(kw) :]
        if len(k) == 0:
            return keywords[1:]
        keywords[0] = k
        return keywords

    @classmethod
    def unlinked_fragment_search(cls, keywords):
        qs = Fragment.objects.filter(antiquarian_fragmentlinks=None)
        kws = keywords.split()
        ids = cls.remove_keyword("u", kws)
        if ids is None or 1 < len(ids):
            return qs.none()
        if len(ids) == 0:
            return qs
        if not ids[0].isnumeric():
            return qs.none()
        return qs.filter(id__startswith=int(ids[0]))

    @classmethod
    def anonymous_fragment_search(cls, keywords):
        qs = AnonymousFragment.objects.all()
        kws = keywords.split()
        ids = cls.remove_keyword("f", kws)
        if ids is None or 1 < len(ids):
            return qs.none()
        if len(ids) == 0:
            return qs
        if not ids[0].isnumeric():
            return qs.none()
        return qs.filter(order=int(ids[0]) - 1)

    @classmethod
    def testimonium_search(cls, keywords):
        qs = Testimonium.objects.all()
        results = qs.filter(
            antiquarian_testimoniumlinks__antiquarian__name__icontains=keywords  # noqa
        )
        return results.distinct()

    @classmethod
    def bibliography_search(cls, keywords):
        results = BibliographyItem.objects.filter(
            Q(authors__icontains=keywords) | Q(title__icontains=keywords)
        )
        return results.distinct()

    def get(self, request, *args, **kwargs):

        ajax_data = []

        from django.apps import apps

        dd = apps.all_models["research"]
        model_name_cache = {}

        # return just the name, pk and type for display
        for o in self.get_queryset():
            model_name = model_name_cache.get(o.__class__, None)
            if not model_name:
                model_name = next(k for k, value in dd.items() if value == o.__class__)
                model_name_cache[o.__class__] = model_name

            ajax_data.append({"id": o.pk, "target": model_name, "value": str(o)})

        return JsonResponse(data=ajax_data, safe=False)

    def parse_mention(self, q):
        # split string at colon
        search_terms = q.split(":")
        method = search_terms.pop(0)
        return method, search_terms

    def get_queryset(self):
        method, search_terms = self.parse_mention(self.request.GET.get("q"))

        # check if method is in the search method keys eg aq, tt, etc, if not return an empty list
        if method in self.SEARCH_METHODS.keys():
            # call method with list of search terms
            return self.SEARCH_METHODS[method](search_terms)
        else:
            return []

        # keywords = self.request.GET.get("q")
        # if not keywords:
        #     return []

        # result_set = []
        # to_search = self.SEARCH_METHODS.keys()
        # for what in to_search:
        #     result_set.append(self.SEARCH_METHODS[what](keywords))

        # queryset_chain = chain(*result_set)

        # # return a of results
        # return sorted(queryset_chain, key=lambda instance: instance.pk, reverse=True)
