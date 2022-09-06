# from django.contrib.postgres.search import SearchQuery, SearchRank, \
#     SearchVector

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Concat
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
    def BASIC_SEARCH_METHODS(self):
        return {
            "aq": self.basic_search,
            "tt": self.basic_search,
            "tp": self.basic_search,
            "wk": self.basic_search,
        }

    @property
    def BASIC_SEARCH_TYPES(self):
        return {
            "aq": [Antiquarian, "name__icontains"],
            "tt": [
                Testimonium,
                "antiquarian_testimoniumlinks__antiquarian__name__icontains",
            ],
            "tp": [Topic, "name__icontains"],
            "wk": [Work, "name__icontains"],
        }

    @property
    def SPECIAL_SEARCH_METHODS(self):
        return {
            "af": self.anonymous_fragment_search,
            "fr": self.fragment_search,
            "bi": self.bibliography_search,
            "uf": self.unlinked_fragment_search,
        }

    def order_number_search(keywords):
        order_number = None
        for kw in keywords:
            if kw.isnumeric():
                order_number = int(kw)
                keywords.remove(kw)
        return order_number, keywords

    @classmethod
    def basic_search(cls, self, method, keywords):
        target_model = self.BASIC_SEARCH_TYPES[method][0]
        filter_slug = self.BASIC_SEARCH_TYPES[method][1]

        model_query = Q()
        for kw in keywords:
            model_query = model_query & Q(**{filter_slug: kw})

        qs = target_model.objects.all()
        results = qs.filter(model_query)
        return results.distinct()

    @classmethod
    def anonymous_fragment_search(cls, keywords):
        # do we want to make it so the search is inclusive, not exact?
        # i.e @af:1 returns 1,10,11,etc
        order_number = cls.order_number_search(keywords)[0]
        qs = AnonymousFragment.objects.all()
        if order_number:
            order_number = order_number - 1
            order_query = Q(id=order_number) | Q(order=order_number)
        else:
            order_query = Q()

        results = qs.filter(order_query)
        return results.distinct()

    @classmethod
    def bibliography_search(cls, keywords):
        qs = BibliographyItem.objects.annotate(
            author_title=Concat(
                F("authors"), Value(" "), F("title"), output_field=CharField()
            )
        )
        bib_query = Q()
        for kw in keywords:
            bib_query = bib_query & Q(author_title__icontains=kw)

        results = qs.filter(bib_query)
        return results.distinct()

    @classmethod
    def fragment_search(cls, keywords):
        # if the keyword is a number then use order number search
        order_number, antiquarian = cls.order_number_search(keywords)
        qs = Fragment.objects.filter(antiquarian_fragmentlinks__isnull=False)

        if order_number:
            order_number = order_number - 1
            """either the antiquarian order number is
             the order number or the work order number is the order number"""
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
    def unlinked_fragment_search(cls, keywords):
        order_number = cls.order_number_search(keywords)[0]
        qs = Fragment.objects.filter(antiquarian_fragmentlinks=None)
        if order_number:
            order_query = Q(id__startswith=order_number)
        else:
            order_query = Q()

        results = qs.filter(order_query)
        return results.distinct()

    def get(self, request, *args, **kwargs):
        ajax_data = []

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
        search_terms = q.split(":")
        method = search_terms.pop(0)
        return method, search_terms

    def get_queryset(self):
        if self.request.GET.get("q") is None:
            return []

        method, search_terms = self.parse_mention(self.request.GET.get("q"))
        # check if method is in the search method keys
        # eg aq, tt, etc, if not return an empty list
        if method in self.BASIC_SEARCH_METHODS.keys():
            # call method with list of search terms
            return self.BASIC_SEARCH_METHODS[method](
                self=self, method=method, keywords=search_terms
            )

        elif method in self.SPECIAL_SEARCH_METHODS.keys():
            return self.SPECIAL_SEARCH_METHODS[method](search_terms)

        else:
            return []
