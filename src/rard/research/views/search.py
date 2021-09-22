# from django.contrib.postgres.search import SearchQuery, SearchRank, \
#     SearchVector
from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import ListView, TemplateView

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    Fragment,
    Testimonium,
    Topic,
    Work,
)
from rard.research.models.citing_work import CitingAuthor, CitingWork


@method_decorator(require_GET, name="dispatch")
class SearchView(LoginRequiredMixin, TemplateView, ListView):

    paginate_by = 10
    template_name = "research/search_results.html"
    context_object_name = "results"

    @property
    def SEARCH_METHODS(self):
        return {
            "antiquarians": self.antiquarian_search,
            "testimonia": self.testimonium_search,
            "anonymous fragments": self.anonymous_fragment_search,
            "fragments": self.fragment_search,
            "topics": self.topic_search,
            "works": self.work_search,
            "bibliographies": self.bibliography_search,
            "apparatus critici": self.apparatus_criticus_search,
            "apposita": self.appositum_search,
            "citing authors": self.citing_author_search,
            "citing works": self.citing_work_search,
        }

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, keywords):
        qs = Antiquarian.objects.all()
        results = (
            qs.filter(name__icontains=keywords)
            | qs.filter(introduction__content__icontains=keywords)
            | qs.filter(re_code__icontains=keywords)
        )
        return results.distinct()

    @classmethod
    def topic_search(cls, keywords):
        qs = Topic.objects.all()
        results = qs.filter(name__icontains=keywords)
        return results.distinct()

    @classmethod
    def work_search(cls, keywords):
        qs = Work.objects.all()
        results = (
            qs.filter(name__icontains=keywords)
            | qs.filter(subtitle__icontains=keywords)
            | qs.filter(antiquarian__name__icontains=keywords)
        )
        return results.distinct()

    @classmethod
    def fragment_search(cls, keywords):
        qs = Fragment.objects.all()
        results = (
            qs.filter(original_texts__content__icontains=keywords)
            | qs.filter(original_texts__reference__icontains=keywords)
            | qs.filter(
                original_texts__translation__translated_text__icontains=keywords
            )
            | qs.filter(  # noqa
                original_texts__translation__translator_name__icontains=keywords
            )
            | qs.filter(commentary__content__icontains=keywords)  # noqa
        )
        return results.distinct()

    @classmethod
    def anonymous_fragment_search(cls, keywords, qs=None):
        if not qs:
            qs = AnonymousFragment.objects.all()
        results = (
            qs.filter(original_texts__content__icontains=keywords)
            | qs.filter(original_texts__reference__icontains=keywords)
            | qs.filter(
                original_texts__translation__translated_text__icontains=keywords
            )
            | qs.filter(  # noqa
                original_texts__translation__translator_name__icontains=keywords
            )
            | qs.filter(commentary__content__icontains=keywords)  # noqa
        )
        return results.distinct()

    @classmethod
    def testimonium_search(cls, keywords):
        qs = Testimonium.objects.all()
        results = (
            qs.filter(original_texts__content__icontains=keywords)
            | qs.filter(original_texts__reference__icontains=keywords)
            | qs.filter(
                original_texts__translation__translated_text__icontains=keywords
            )
            | qs.filter(  # noqa
                original_texts__translation__translator_name__icontains=keywords
            )
            | qs.filter(commentary__content__icontains=keywords)  # noqa
        )
        return results.distinct()

    @classmethod
    def apparatus_criticus_search(cls, keywords):
        qst = Testimonium.objects.all()
        qsa = AnonymousFragment.objects.all()
        qsf = Fragment.objects.all()
        return chain(
            qsf.filter(
                original_texts__apparatus_criticus_items__content__icontains=keywords
            ).distinct(),  # noqa
            qsa.filter(
                original_texts__apparatus_criticus_items__content__icontains=keywords
            ).distinct(),  # noqa
            qst.filter(
                original_texts__apparatus_criticus_items__content__icontains=keywords
            ).distinct(),  # noqa
        )

    @classmethod
    def bibliography_search(cls, keywords):
        qs = BibliographyItem.objects.all()
        results = qs.filter(authors__icontains=keywords) | qs.filter(
            title__icontains=keywords
        )
        return results.distinct()

    @classmethod
    def appositum_search(cls, keywords):
        qs = AnonymousFragment.objects.exclude(appositumfragmentlinks_from=None).all()
        return cls.anonymous_fragment_search(keywords, qs=qs)

    @classmethod
    def citing_author_search(cls, keywords):
        qs = CitingAuthor.objects.all()
        return qs.filter(name__icontains=keywords).distinct()

    @classmethod
    def citing_work_search(cls, keywords):
        qs = CitingWork.objects.all()
        results = qs.filter(title__icontains=keywords) | qs.filter(
            edition__icontains=keywords
        )
        return results.distinct()

    def get(self, request, *args, **kwargs):
        keywords = self.request.GET.get("q", None)
        if keywords is not None and keywords.strip() == "":
            # empty search field. Redirect to cleared page
            ret = redirect(self.request.path)
        else:
            ret = super().get(request, *args, **kwargs)

        return ret

    def get_context_data(self, *args, **kwargs):
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()
        context = super().get_context_data(*args, **kwargs)
        keywords = self.request.GET.get("q")
        to_search = self.request.GET.getlist("what")
        context["search_term"] = keywords
        context["to_search"] = to_search
        context["search_classes"] = self.SEARCH_METHODS.keys()

        return context

    def get_queryset(self):
        keywords = self.request.GET.get("q")
        if not keywords:
            return []

        result_set = []

        to_search = self.request.GET.getlist("what", ["all"])
        if to_search == ["all"]:
            to_search = self.SEARCH_METHODS.keys()

        for what in to_search:
            result_set.append(self.SEARCH_METHODS[what](keywords))

        queryset_chain = chain(*result_set)

        # return a list...
        return sorted(queryset_chain, key=lambda instance: instance.pk, reverse=True)
