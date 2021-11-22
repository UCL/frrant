import re
from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ExpressionWrapper, Func, Q, TextField, Value
from django.db.models.functions import Lower
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

# Fold [X,Y] transforms all instances of Y into X before matching
# Folds are applied in the specified order, so we don't need
# 'uul' <- 'vul' if we already have 'u' <- 'v'
rard_folds = [
    ["ast", "a est"],
    ["ost", "o est"],
    ["umst", "um est"],
    ["am", "an"],
    ["ausa", "aussa"],
    ["nn", "bn"],
    ["tt", "bt"],
    ["pp", "bp"],
    ["rr", "br"],
    ["ch", "cch"],
    ["clu", "culu"],
    ["claud", "clod"],
    ["has", "hasce"],
    ["his", "hisce"],
    ["hos", "hosce"],
    ["i", "ii"],
    ["i", "j"],
    ["um", "im"],
    ["lagr", "lagl"],
    ["mb", "nb"],
    ["ll", "nl"],
    ["mm", "nm"],
    ["mp", "np"],
    ["mp", "ndup"],
    ["rr", "nr"],
    ["um", "om"],
    ["u", "v"],
    ["u", "y"],
    ["uu", "w"],
    ["ulc", "ulch"],
    ["uul", "uol"],
    ["ui", "uui"],
    ["uum", "uom"],
    ["x", "xs"],
]

PUNCTUATION_BASE = r"!£$%^&*()_+-={}:@~;\'#|\\<>?,./`¬"
PUNCTUATION_RE = re.compile(r"[\[\]{0}]".format(PUNCTUATION_BASE))
PUNCTUATION = PUNCTUATION_BASE + r'[]"'


@method_decorator(require_GET, name="dispatch")
class SearchView(LoginRequiredMixin, TemplateView, ListView):
    class Term:
        """
        Initialize it with the keywords:
        term = Term(keywords)
        and you call:
        results = term.match('foreign_key_1__foreign_key_2__field')
        or:
        results = term.match_folded('foreign_key_1__foreign_key_2__field')
        """

        def __init__(self, keywords):
            self.cleaned_number = 1
            self.folded_number = 1
            self.keywords = PUNCTUATION_RE.sub("", keywords).lower()
            # The basic function query function will first eliminate html less than
            # and greater than character codes, then punctuation,
            # and lowercase the 'haystack' strings to be searched.
            self.basic_query = lambda q: Lower(
                Func(
                    Func(q, Value("&[gl]t;"), Value(""), function="regexp_replace"),
                    Value(PUNCTUATION),
                    Value(""),
                    function="translate",
                )
            )
            self.query = self.basic_query
            # Now we call add_fold repeatedly to add more
            # folds to self.query
            k = self.keywords
            for (fold_to, fold_from) in rard_folds:
                if fold_from in k:
                    k = k.replace(fold_from, fold_to)
                    self.add_fold(fold_from, fold_to)
                elif fold_to in k:
                    self.add_fold(fold_from, fold_to)
            self.folded_matcher = self.get_matcher(k)
            self.nonfolded_matcher = self.get_matcher(self.keywords)

        def get_matcher(self, keywords):
            keyword_list = self.get_keywords(keywords)
            if len(keyword_list) == 0:
                # want a keyword that will always succeed
                first_keyword = ""
            else:
                first_keyword = keyword_list[0]
                keyword_list = keyword_list[1:]

            def matcher(field):
                return Q(**{field: first_keyword})

            for keyword in keyword_list:
                matcher = self.add_keyword(matcher, keyword)
            return matcher

        def add_keyword(self, old, keyword):
            return lambda f: Q(**{f: keyword}) & old(f)

        def add_fold(self, fold_from, fold_to):
            old = self.query
            self.query = lambda q: Func(
                old(q), Value(fold_from), Value(fold_to), function="replace"
            )

        def get_keywords(self, search_string):
            """
            Turns a string into a series of keywords. This is mostly splittling
            by whitespace, but strings surrounded by double quotes are
            returned verbatim.
            """
            segments = search_string.split('"')
            single_keywords = " ".join(segments[::2]).split()
            return segments[1::2] + single_keywords

        def do_match(self, query_set, query_string, annotation_name, query, matcher):
            expression = ExpressionWrapper(
                query(query_string), output_field=TextField()
            )
            annotated = query_set.annotate(**{annotation_name: expression})
            return annotated.filter(matcher(annotation_name + "__contains"))

        def match(self, query_set, query_string):
            annotation_name = "cleaned{0}".format(self.cleaned_number)
            self.cleaned_number += 1
            return self.do_match(
                query_set,
                query_string,
                annotation_name,
                self.basic_query,
                self.nonfolded_matcher,
            )

        def match_folded(self, query_set, query_string):
            annotation_name = "folded{0}".format(self.folded_number)
            self.folded_number += 1
            return self.do_match(
                query_set,
                query_string,
                annotation_name,
                self.query,
                self.folded_matcher,
            )

    paginate_by = 10
    template_name = "research/search_results.html"
    context_object_name = "results"

    @property
    def SEARCH_METHODS(self):
        return {
            "anonymous fragments": self.anonymous_fragment_search,
            "antiquarians": self.antiquarian_search,
            "apparatus critici": self.apparatus_criticus_search,
            "apposita": self.appositum_search,
            "bibliographies": self.bibliography_search,
            "citing authors": self.citing_author_search,
            "citing works": self.citing_work_search,
            "fragments": self.fragment_search,
            "testimonia": self.testimonium_search,
            "topics": self.topic_search,
            "works": self.work_search,
        }

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, terms):
        qs = Antiquarian.objects.all()
        results = (
            terms.match(qs, "name")
            | terms.match(qs, "introduction__content")
            | terms.match(qs, "re_code")
        )
        return results.distinct()

    @classmethod
    def topic_search(cls, terms):
        qs = Topic.objects.all()
        results = terms.match(qs, "name")
        return results.distinct()

    @classmethod
    def work_search(cls, terms):
        qs = Work.objects.all()
        results = (
            terms.match(qs, "name")
            | terms.match(qs, "subtitle")
            | terms.match(qs, "antiquarian__name")
        )
        return results.distinct()

    @classmethod
    def fragment_search(cls, terms):
        qs = Fragment.objects.all()
        results = (
            terms.match_folded(qs, "original_texts__content")
            | terms.match(qs, "original_texts__reference")
            | terms.match(qs, "original_texts__translation__translated_text")  # noqa
            | terms.match(qs, "original_texts__translation__translator_name")  # noqa
            | terms.match_folded(qs, "commentary__content")
        )
        return results.distinct()

    @classmethod
    def anonymous_fragment_search(cls, terms, qs=None):
        if not qs:
            qs = AnonymousFragment.objects.all()
        results = (
            terms.match_folded(qs, "original_texts__content")
            | terms.match(qs, "original_texts__reference")
            | terms.match(qs, "original_texts__translation__translated_text")  # noqa
            | terms.match(qs, "original_texts__translation__translator_name")  # noqa
            | terms.match_folded(qs, "commentary__content")
        )
        return results.distinct()

    @classmethod
    def testimonium_search(cls, terms):
        qs = Testimonium.objects.all()
        results = (
            terms.match_folded(qs, "original_texts__content")
            | terms.match(qs, "original_texts__reference")
            | terms.match(qs, "original_texts__translation__translated_text")  # noqa
            | terms.match(qs, "original_texts__translation__translator_name")  # noqa
            | terms.match_folded(qs, "commentary__content")
        )
        return results.distinct()

    @classmethod
    def apparatus_criticus_search(cls, terms):
        query_string = "original_texts__apparatus_criticus_items__content"
        qst = Testimonium.objects.all()
        qsa = AnonymousFragment.objects.all()
        qsf = Fragment.objects.all()
        return chain(
            terms.match_folded(qsf, query_string).distinct(),
            terms.match_folded(qsa, query_string).distinct(),
            terms.match_folded(qst, query_string).distinct(),
        )

    @classmethod
    def bibliography_search(cls, terms):
        qs = BibliographyItem.objects.all()
        results = terms.match(qs, "authors") | terms.match(qs, "title")
        return results.distinct()

    @classmethod
    def appositum_search(cls, terms):
        qs = AnonymousFragment.objects.exclude(appositumfragmentlinks_from=None).all()
        return cls.anonymous_fragment_search(terms, qs=qs)

    @classmethod
    def citing_author_search(cls, terms):
        qs = CitingAuthor.objects.all()
        return terms.match(qs, "name").distinct()

    @classmethod
    def citing_work_search(cls, terms):
        qs = CitingWork.objects.all()
        results = terms.match(qs, "title") | terms.match(qs, "edition")
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

        terms = SearchView.Term(keywords)

        result_set = []

        to_search = self.request.GET.getlist("what", ["all"])
        if to_search == ["all"]:
            to_search = self.SEARCH_METHODS.keys()

        for what in to_search:
            result_set.append(self.SEARCH_METHODS[what](terms))

        queryset_chain = chain(*result_set)

        # return a list...
        return sorted(queryset_chain, key=lambda instance: instance.pk, reverse=True)
