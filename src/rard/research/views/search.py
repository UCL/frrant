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
                    Func(
                        q,
                        Value("&[gl]t;"),
                        Value(""),
                        Value("g"),
                        function="regexp_replace",
                    ),
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
            self.folded_keywords = k
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

        def do_match(
            self,
            query_set,
            query_string,
            annotation_name,
            query,
            matcher,
            keywords,
            add_snippet=False,
        ):
            expression = ExpressionWrapper(
                query(query_string), output_field=TextField()
            )
            annotated = query_set.annotate(**{annotation_name: expression})
            matches = annotated.filter(matcher(annotation_name + "__contains"))
            if add_snippet:
                matches = self.annotate_with_snippet(matches, keywords, query_string)
            else:
                matches = matches.annotate(snippet=Value(""))
            return matches

        def annotate_with_snippet(self, qs, keywords, query_string):
            return qs.annotate(
                snippet=Func(
                    Func(
                        Func(
                            Func(
                                Func(
                                    query_string,
                                    Value(self.get_snippet_regex(keywords)),
                                    Value(
                                        r'START_SNIPPET\1<span class="search-snippet">'
                                        r"\2</span>\3...END_SNIPPET"
                                    ),
                                    Value("gi"),
                                    function="REGEXP_REPLACE",
                                ),
                                Value("^((?!START_SNIPPET).)*$"),
                                Value(""),
                                function="REGEXP_REPLACE",
                            ),
                            Value("^.*?START_SNIPPET"),
                            Value(""),
                            Value("gs"),
                            function="REGEXP_REPLACE",
                        ),
                        Value("END_SNIPPET.*?(START_SNIPPET)"),
                        Value(""),
                        Value("gs"),
                        function="REGEXP_REPLACE",
                    ),
                    Value("END_SNIPPET.*"),
                    Value(""),
                    function="REGEXP_REPLACE",
                    output_field=TextField(),
                )
            )

        def get_snippet_regex(self, keywords, before=5, after=5):
            """This regex should give us three capturing groups we can use
            with postgres REGEXP_REPLACE to insert <span> tags around our keywords;
            e.g. REGEXP_REPLACE('content',headline_regex,'\1 <span>\2</span>\3')
            """
            keywords = self.get_keywords(keywords)
            words_before_group = rf"((?:\S+\s){{0,{before}}})"
            keywords_group = "|".join([r"\S*" + kw + r"\S*" for kw in keywords])
            keywords_group = r"(" + keywords_group + r")"
            words_after_group = rf"(\s(?:\S+\s){{0,{after}}})"
            return words_before_group + keywords_group + words_after_group

        def match(self, query_set, query_string, add_snippet=False):
            annotation_name = "cleaned{0}".format(self.cleaned_number)
            self.cleaned_number += 1
            return self.do_match(
                query_set,
                query_string,
                annotation_name,
                self.basic_query,
                self.nonfolded_matcher,
                self.keywords,
                add_snippet=add_snippet,
            )

        def match_folded(self, query_set, query_string, add_snippet=False):
            annotation_name = "folded{0}".format(self.folded_number)
            self.folded_number += 1
            keywords = self.keywords + " " + self.folded_keywords
            return self.do_match(
                query_set,
                query_string,
                annotation_name,
                self.query,
                self.folded_matcher,
                keywords,
                add_snippet=add_snippet,
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

    @classmethod
    def generic_content_search(cls, qs, search_fields):
        results = []
        for field in search_fields:
            field_name, match_function = field
            matches = match_function(qs, field_name, add_snippet=True)
            results.append(matches)
            qs = qs.exclude(id__in=[o.id for o in matches])
        return chain(*results)

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, terms, ant_filter):
        qs = Antiquarian.objects.all()
        search_fields = [
            ("name", terms.match),
            ("plain_introduction", terms.match),
            ("re_code", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def topic_search(cls, terms, ant_filter):
        qs = Topic.objects.all()
        search_fields = [("name", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def work_search(cls, terms, ant_filter):
        qs = Work.objects.all()
        search_fields = [
            ("name", terms.match),
            ("subtitle", terms.match),
            ("antiquarian__name", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def original_text_owner_search(cls, terms, qs):
        search_fields = [
            ("original_texts__plain_content", terms.match_folded),
            ("original_texts__translation__plain_translated_text", terms.match),
            ("plain_commentary", terms.match),
            ("original_texts__translation__translator_name", terms.match),
            ("original_texts__reference", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def fragment_search(cls, terms, ant_filter):
        qs = Fragment.objects.all()
        if ant_filter:
            qs = qs.filter(linked_antiquarians__in=ant_filter)
        return cls.original_text_owner_search(terms, qs)

    @classmethod
    def anonymous_fragment_search(cls, terms, ant_filter, qs=None):
        if not qs:
            qs = AnonymousFragment.objects.all()
        return cls.original_text_owner_search(terms, qs)

    @classmethod
    def testimonium_search(cls, terms, ant_filter):
        qs = Testimonium.objects.all()
        if ant_filter:
            qs = qs.filter(linked_antiquarians__in=ant_filter)
        return cls.original_text_owner_search(terms, qs)

    @classmethod
    def apparatus_criticus_search(cls, terms, ant_filter):
        query_string = "original_texts__apparatus_criticus_items__content"
        qst = Testimonium.objects.all()
        qsa = AnonymousFragment.objects.all()
        qsf = Fragment.objects.all()
        return chain(
            terms.match_folded(qsf, query_string, add_snippet=True).distinct(),
            terms.match_folded(qsa, query_string, add_snippet=True).distinct(),
            terms.match_folded(qst, query_string, add_snippet=True).distinct(),
        )

    @classmethod
    def bibliography_search(cls, terms, ant_filter):
        qs = BibliographyItem.objects.all()
        results = terms.match(qs, "authors") | terms.match(qs, "title")
        return results.distinct()

    @classmethod
    def appositum_search(cls, terms, ant_filter):
        qs = AnonymousFragment.objects.exclude(appositumfragmentlinks_from=None).all()
        return cls.anonymous_fragment_search(terms, ant_filter, qs=qs)

    @classmethod
    def citing_author_search(cls, terms, ant_filter):
        qs = CitingAuthor.objects.all()
        return terms.match(qs, "name").distinct()

    @classmethod
    def citing_work_search(cls, terms, ant_filter):
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
        context["antiquarians"] = self.get_antiquarian_list(self.object_list)
        context["search_term"] = keywords
        context["to_search"] = to_search
        context["search_classes"] = self.SEARCH_METHODS.keys()

        return context

    def get_queryset(self):
        keywords = self.request.GET.get("q")
        ant_filter = self.request.GET.getlist("ant")
        if not keywords:
            return []

        terms = SearchView.Term(keywords)

        result_set = []

        to_search = self.request.GET.getlist("what", ["all"])
        if to_search == ["all"]:
            to_search = self.SEARCH_METHODS.keys()

        for what in to_search:
            result_set.append(self.SEARCH_METHODS[what](terms, ant_filter))

        queryset_chain = chain(*result_set)

        # return a list...
        return sorted(queryset_chain, key=lambda instance: instance.pk, reverse=True)

    def get_antiquarian_list(self, queryset):
        antiquarians = []
        if queryset:
            for material in queryset:
                mtype = material.__class__.__name__
                if mtype in ["Fragment", "Testimonium"]:
                    antiquarians.extend(
                        list(material.linked_antiquarians.distinct().all())
                    )
        else:
            antiquarians = list(Antiquarian.objects.all())
        return set(antiquarians)
