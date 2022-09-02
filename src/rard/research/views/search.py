import re
from functools import partial
from itertools import chain

from django.conf import settings
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
    CitingAuthor,
    CitingWork,
    Fragment,
    Testimonium,
    Topic,
    Work,
)

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

WILDCARD_SINGLE_CHAR = settings.WILDCARD_SINGLE_CHAR
WILDCARD_MANY_CHAR = settings.WILDCARD_MANY_CHAR
WILDCARD_CHARS = [WILDCARD_SINGLE_CHAR, WILDCARD_MANY_CHAR]
PUNCTUATION_BASE = r"!£$%^&*()_+-={}:@~;\'#|\\<>?,./`¬"
# Remove wildcard characters from PUNCTUATION_BASE which is used to screen
# out punctuation from search terms
PUNCTUATION_BASE = PUNCTUATION_BASE.translate({ord(c): None for c in WILDCARD_CHARS})
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
            # Remove all punctuation except * and ?
            self.keywords = PUNCTUATION_RE.sub("", keywords).lower()
            # If wildcard characters appear in keywords, use regex lookup
            if any([char in self.keywords for char in WILDCARD_CHARS]):
                self.lookup = "regex"
            else:
                self.lookup = "contains"
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
            returned verbatim. Each keywords is converted to a regular expression
            if self.lookup is regex.
            """
            segments = search_string.split('"')
            single_keywords = " ".join(segments[::2]).split()
            keywords = segments[1::2] + single_keywords
            if self.lookup == "regex":
                keywords = self.transform_keywords_to_regex(keywords)
            return keywords

        def transform_keywords_to_regex(self, keywords):
            """Takes a list of keywords which may include wildcard characters
            and converts them into a list of equivalent regular expressions.
            Example:
            >>> transform_keywords_to_regex(["?ulius", "c*sar"])
            ["\\m\\wulius\\M", "\\mc\\w*sar\\M"]

            :param keywords: A list of strings to search
            :type keywords: list
            :return: list of regular expressions
            :rtype: list
            """
            for i, kw in enumerate(keywords):
                reg_kw = r"\m"  # \m matches start of word
                for char in kw:
                    if char == WILDCARD_SINGLE_CHAR:
                        reg_kw += r"\w"  # a single word char (greek chars work here)
                    elif char == WILDCARD_MANY_CHAR:
                        reg_kw += r"\w*"  # zero or more word characters
                    else:
                        reg_kw += char
                reg_kw += r"\M"  # \M matches end of word
                keywords[i] = reg_kw
            return keywords

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
            matches = annotated.filter(matcher(annotation_name + "__" + self.lookup))
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

    class SearchMethodGroup:
        """Initialise this with a group name (e.g. fragments) and
        the core method to be modified using functools.partial; e.g.
        fragment_search_methods = SearchMethodGroup("fragments", fragment_search)

        The core method should accept the search_field keyword argument
        which can override the default set of search fields the core method
        would normally use.

        A default_method property returns the method to be used to search all
        content.

        A display_list property returns:
        [group_name, "all content", "orginal texts", "translations", "commentary"]
        """

        search_types = [
            ("all content", None),
            ("original texts", ["original_texts__plain_content", "folded"]),
            (
                "translations",
                [
                    "original_texts__translation__plain_translated_text",
                    "non-folded",
                ],
            ),
            ("commentary", ["plain_commentary", "non-folded"]),
        ]

        def __init__(self, group_name, core_method):
            self.group_name = group_name
            self.methods = {}
            for content_field, search_field in self.search_types:
                self.methods[f"{group_name}_{content_field}"] = partial(
                    core_method, search_field=search_field
                )
            self.default_method_name = f"{group_name}_{self.search_types[0][0]}"

        @property
        def default_method(self):
            return {self.default_method_name: self.methods[self.default_method_name]}

        @property
        def display_list(self):
            return [self.group_name] + [type[0] for type in self.search_types]

    @property
    def SEARCH_METHODS(self):
        fragment_search_methods = self.SearchMethodGroup(
            "fragments", self.fragment_search
        )
        testimonia_search_methods = self.SearchMethodGroup(
            "testimonia", self.testimonium_search
        )
        apposita_search_methods = self.SearchMethodGroup(
            "apposita", self.appositum_search
        )
        anon_fragment_search_methods = self.SearchMethodGroup(
            "anonymous fragments", self.anonymous_fragment_search
        )
        single_methods = {
            "antiquarians": self.antiquarian_search,
            "apparatus critici": self.apparatus_criticus_search,
            "bibliographies": self.bibliography_search,
            "citing authors": self.citing_author_search,
            "citing works": self.citing_work_search,
            "topics": self.topic_search,
            "works": self.work_search,
        }
        all_methods = {
            **single_methods,
            **fragment_search_methods.methods,
            **testimonia_search_methods.methods,
            **apposita_search_methods.methods,
            **anon_fragment_search_methods.methods,
        }
        default_methods = {
            **single_methods,
            **fragment_search_methods.default_method,
            **testimonia_search_methods.default_method,
            **apposita_search_methods.default_method,
            **anon_fragment_search_methods.default_method,
        }
        display_list = (
            [[key] for key in single_methods.keys()]
            + [fragment_search_methods.display_list]
            + [testimonia_search_methods.display_list]
            + [apposita_search_methods.display_list]
            + [anon_fragment_search_methods.display_list]
        )
        return {
            "all_methods": all_methods,
            "default_methods": default_methods,
            "display_list": display_list,
        }

    @classmethod
    def generic_content_search(cls, qs, search_fields):
        results = []
        for field in search_fields:
            field_name, match_function = field
            matches = match_function(qs, field_name, add_snippet=True)
            results.append(matches)
            # Remove objects from queryset once matched so they don't get matched twice
            qs = qs.exclude(id__in=[o.id for o in matches])
        return chain(*results)

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, terms, ant_filter=None, **kwargs):
        qs = cls.get_filtered_model_qs(Antiquarian, ant_filter=ant_filter)
        search_fields = [
            ("name", terms.match),
            ("plain_introduction", terms.match),
            ("re_code", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def topic_search(cls, terms, **kwargs):
        qs = Topic.objects.all()
        search_fields = [("name", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def work_search(cls, terms, ant_filter=None, **kwargs):
        qs = cls.get_filtered_model_qs(Work, ant_filter=ant_filter)
        search_fields = [
            ("name", terms.match),
            ("subtitle", terms.match),
            ("antiquarian__name", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def original_text_owner_search(cls, terms, qs, search_field=None):
        if search_field:
            match_function = (
                terms.match_folded if search_field[1] == "folded" else terms.match
            )
            search_fields = [(search_field[0], match_function)]
        else:
            search_fields = [
                ("original_texts__plain_content", terms.match_folded),
                ("original_texts__translation__plain_translated_text", terms.match),
                ("plain_commentary", terms.match),
                ("original_texts__translation__translator_name", terms.match),
                ("original_texts__references__reference_position", terms.match),
                ("original_texts__references__editor", terms.match),
            ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def fragment_search(
        cls, terms, ant_filter=None, ca_filter=None, search_field=None, **kwargs
    ):
        qs = cls.get_filtered_model_qs(
            Fragment, ant_filter=ant_filter, ca_filter=ca_filter
        )
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def testimonium_search(
        cls, terms, ant_filter=None, ca_filter=None, search_field=None, **kwargs
    ):
        qs = cls.get_filtered_model_qs(
            Testimonium, ant_filter=ant_filter, ca_filter=ca_filter
        )
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def anonymous_fragment_search(
        cls,
        terms,
        ant_filter=None,
        ca_filter=None,
        search_field=None,
        qs=None,
        **kwargs,
    ):
        if not qs:
            qs = cls.get_filtered_model_qs(
                AnonymousFragment, ant_filter=ant_filter, ca_filter=ca_filter
            )
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def appositum_search(
        cls, terms, ant_filter=None, ca_filter=None, search_field=None, **kwargs
    ):
        qs = AnonymousFragment.objects.exclude(appositumfragmentlinks_from=None).all()
        qs = cls.get_filtered_model_qs(
            AnonymousFragment, qs=qs, ant_filter=ant_filter, ca_filter=ca_filter
        )
        return cls.anonymous_fragment_search(
            terms, qs=qs, search_field=search_field, **kwargs
        )

    @classmethod
    def apparatus_criticus_search(
        cls, terms, ant_filter=None, ca_filter=None, **kwargs
    ):
        query_string = "original_texts__apparatus_criticus_items__content"
        qst = cls.get_filtered_model_qs(
            Testimonium, ant_filter=ant_filter, ca_filter=ca_filter
        )
        qsa = cls.get_filtered_model_qs(
            AnonymousFragment, ant_filter=ant_filter, ca_filter=ca_filter
        )
        qsf = cls.get_filtered_model_qs(
            Fragment, ant_filter=ant_filter, ca_filter=ca_filter
        )
        return chain(
            terms.match_folded(qsf, query_string, add_snippet=True).distinct(),
            terms.match_folded(qsa, query_string, add_snippet=True).distinct(),
            terms.match_folded(qst, query_string, add_snippet=True).distinct(),
        )

    @classmethod
    def bibliography_search(cls, terms, ant_filter=None, **kwargs):
        qs = cls.get_filtered_model_qs(BibliographyItem, ant_filter=ant_filter)
        search_fields = [("authors", terms.match), ("title", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def citing_author_search(cls, terms, ca_filter=None, **kwargs):
        qs = cls.get_filtered_model_qs(CitingAuthor, ca_filter=ca_filter)
        search_fields = [("name", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def citing_work_search(cls, terms, ca_filter=None, **kwargs):
        qs = cls.get_filtered_model_qs(CitingWork, ca_filter=ca_filter)
        search_fields = [("title", terms.match), ("edition", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def get_filtered_model_qs(cls, model, qs=None, ant_filter=None, ca_filter=None):
        if not qs:
            qs = model.objects.all()
        if ant_filter:
            if model in [Fragment, Testimonium]:
                qs = qs.filter(linked_antiquarians__in=ant_filter)
            if model == AnonymousFragment:
                qs = qs.filter(appositumfragmentlinks_from__antiquarian__in=ant_filter)
            if model == Antiquarian:
                qs = qs.filter(id__in=ant_filter)
            if model == Work:
                qs = qs.filter(antiquarian__in=ant_filter)
            if model == BibliographyItem:
                qs = qs.filter(bibliography_items__in=ant_filter)
        if ca_filter:
            if model in [Fragment, AnonymousFragment, Testimonium]:
                qs = qs.filter(original_texts__citing_work__author__in=ca_filter)
            if model == CitingWork:
                qs = qs.filter(author__in=ca_filter)
            if model == CitingAuthor:
                qs = qs.filter(id__in=ca_filter)
        return qs

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
        context["ant_filter"] = self.request.GET.getlist("ant")
        (
            context["antiquarians"],
            context["authors"],
        ) = self.antiquarians_and_authors_in_object_list(self.object_list)
        context["ca_filter"] = self.request.GET.getlist("ca")
        context["search_term"] = keywords
        context["to_search"] = to_search
        context["search_classes"] = self.SEARCH_METHODS["display_list"]

        return context

    def get_queryset(self):
        keywords = self.request.GET.get("q")
        filter_kwargs = {
            "ant_filter": self.request.GET.getlist("ant"),
            "ca_filter": self.request.GET.getlist("ca"),
        }
        if not keywords:
            return []

        terms = SearchView.Term(keywords)

        result_set = []

        to_search = self.request.GET.getlist("what", ["all"])
        if to_search == ["all"]:
            # Use default methods rather than all because we don't want
            # to search same fragment several times with different methods
            to_search = self.SEARCH_METHODS["default_methods"].keys()

        for what in to_search:
            result_set.append(
                self.SEARCH_METHODS["all_methods"][what](terms, **filter_kwargs)
            )

        queryset_chain = chain(*result_set)

        # return a list...
        return sorted(queryset_chain, key=lambda instance: instance.pk, reverse=True)

    def antiquarians_and_authors_in_object_list(self, object_list):
        """Generate lists of Antiquarians and Citing Authors associated with
        the list of objects provided.

        Antiquarians can come from: Fragments, Testimonia, Anonymous Fragments,
        Antiquarians, Bibliography Items, or Works.

        Citing Authors can come from: Fragments, Testimonia, Anonymous
        Fragments, Citing Works, or Citing Authors.
        """
        antiquarians = []
        authors = []
        if object_list:
            for object in object_list:
                obj_type = object.__class__
                if obj_type == Fragment:
                    antiquarians.extend(
                        list(object.linked_antiquarians.distinct().all())
                    )
                    authors.extend(
                        list(
                            CitingAuthor.objects.filter(
                                citingwork__originaltext__fragments=object
                            )
                        )
                    )
                if obj_type == Testimonium:
                    antiquarians.extend(
                        list(object.linked_antiquarians.distinct().all())
                    )
                    authors.extend(
                        list(
                            CitingAuthor.objects.filter(
                                citingwork__originaltext__testimonia=object
                            )
                        )
                    )
                if obj_type == AnonymousFragment:
                    antiquarians.extend(
                        list(
                            Antiquarian.objects.filter(
                                appositumfragmentlinks__anonymous_fragment=object
                            )
                        )
                    )
                    authors.extend(
                        list(
                            CitingAuthor.objects.filter(
                                citingwork__originaltext__anonymous_fragments=object
                            )
                        )
                    )
                elif obj_type == Antiquarian:
                    antiquarians.append(object)
                elif obj_type == BibliographyItem:
                    antiquarians.extend(list(object.bibliography_items.all()))
                elif obj_type == Work:
                    antiquarians.extend(list(object.antiquarian_set.all()))
                elif obj_type == CitingWork:
                    authors.append(object.author)
                elif obj_type == CitingAuthor:
                    authors.append(object)
            # Remove duplicates and sort
            antiquarians = list(set(antiquarians))
            antiquarians.sort(key=lambda x: (x.order_name, x.re_code))
            authors = list(set(authors))
            authors.sort(key=lambda x: x.order_name)
        else:
            # Return all antiquarians and authors (already sorted)
            antiquarians = list(Antiquarian.objects.all())
            authors = list(CitingAuthor.objects.all())
        return antiquarians, authors
