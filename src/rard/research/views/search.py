import re
from collections.abc import Callable, Iterable
from functools import partial
from itertools import chain
from string import punctuation
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Expression, Func, Q, QuerySet, TextField, Value
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import ListView, TemplateView

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    Book,
    CitingAuthor,
    CitingWork,
    Fragment,
    Testimonium,
    Topic,
    Work,
)
from rard.utils.text_processors import fold_latin

WILDCARD_SINGLE_CHAR = settings.WILDCARD_SINGLE_CHAR
WILDCARD_MANY_CHAR = settings.WILDCARD_MANY_CHAR
WILDCARD_PROXIMITY_IND = "~"
WILDCARD_PROXIMITY_SEP = ":"
QUOTE_CHAR = '"'
CTRL_CHARS = [
    WILDCARD_SINGLE_CHAR,
    WILDCARD_MANY_CHAR,
    WILDCARD_PROXIMITY_IND,
    WILDCARD_PROXIMITY_SEP,
    QUOTE_CHAR,
]
PUNCTUATION = punctuation + "£¬"
# PUNCTUATION should include wildcard chars as it is used with content rather than
# search terms
# Remove wildcard characters for PUNCTUATION_BASE which is used to screen
# out punctuation from search terms
PUNCTUATION_BASE = PUNCTUATION.translate({ord(c): None for c in CTRL_CHARS})
PUNCTUATION_RE = re.compile("[" + re.escape(PUNCTUATION_BASE) + "]")

MatcherCallable = Callable[[QuerySet, str, bool], QuerySet]


@method_decorator(require_GET, name="dispatch")
class SearchView(LoginRequiredMixin, TemplateView, ListView):
    class Term:
        """
        The keywords for a search, together with the folds and cleaning
        functions relevant to them.
        """

        def __init__(self, keywords: str):
            """
            Initialize ``Term`` with the keywords.

            :param keywords: The user's query; a string of keywords.
            """
            # Using regex for everything doesn't seem to have a big impact
            # But replace this line with the alternative code if you want to
            # only use regex for search terms containing wildcards
            self.lookup = "iregex"
            # # If wildcard characters appear in keywords, use regex lookup
            # if any([char in keywords for char in CTRL_CHARS]):
            #     self.lookup = "iregex"
            # else:
            #     self.lookup = "icontains"

            # Remove all punctuation except wildcard characers
            keyword_string = PUNCTUATION_RE.sub("", keywords).lower()
            self.keywords = self.get_keywords(keyword_string)

            self.folded_keywords = [fold_latin(keyword) for keyword in self.keywords]

            if self.lookup.endswith("regex"):
                self.keywords = self.transform_keywords_to_regex(self.keywords)
                self.folded_keywords = self.transform_keywords_to_regex(
                    self.folded_keywords
                )

            self.folded_matcher = self.get_matcher(self.folded_keywords)
            self.nonfolded_matcher = self.get_matcher(self.keywords)

        def get_matcher(self, keyword_list: Iterable[str]) -> Callable[[str], Q]:
            """
            Get a matcher for the keyword string.

            :param keywords: The user's input: a string of keywords to search for.
            :return: A function that takes a lookup string and returns an
              expression that matches these keywords in that lookup string.
            """
            if len(keyword_list) == 0:
                # want a query that will always succeed
                return ~Q(pk__in=[])

            def matcher(field: str):
                return Q(**{field: keyword_list[0]})

            for keyword in keyword_list[1:]:
                matcher = self.add_keyword(matcher, keyword)
            return matcher

        def add_keyword(
            self, old: Callable[[str], Q], keyword: str
        ) -> Callable[[str], Q]:
            """
            Add another keyword to a matcher function.

            :param old: Function taking a field name and returning a Django ORM
              function that matches certain keywords.
            :param keyword: New keyword to match.
            :return: Function taking a field name and returning a Django ORM
              function that matches all of the keywords that ``old`` matches plus
              ``keyword`` as well.
            """
            return lambda f: Q(**{f: keyword}) & old(f)

        def get_keywords(self, search_string: str) -> list[str]:
            """
            Turns a string into a series of keywords. This is mostly splitting
            by whitespace, but strings surrounded by double quotes are
            returned verbatim and those containing proximity wildcard consume
            the whole search string. Each keywords is converted to a regular expression.

            Regex alternatives:
            1. Captures whole search string if it contains proximity wildcard (~)
               between two other words.
            2. Captures everything inside double quotes
            3. Captures individual words
            """
            # regex 1st alternative matches proximity, 2nd quoted phrase, 3rd word
            keywords = re.findall(
                r"(.+\s~\d*:?\d*\s.+|(?<=\")[^\"]*(?=\")|[^\s\"]+)", search_string
            )
            return keywords

        def transform_keywords_to_regex(self, keywords):
            """Takes a list of keywords which may include wildcard characters
            and converts them into a list of equivalent regular expressions.
            In the case of proximity search this function is called again to
            handle wildcards.

            Note: these regular expressions are for postgresql which has a
            slightly different syntax to python's re module.

            Examples:
            >>> transform_keywords_to_regex(["?ulius", "c*sar"])
            ["\\m\\wulius\\M", "\\mc\\w*sar\\M"]
            >>> transform_keywords_to_regex(['qua? ~1:2 di*um'])
            ["\\mqua\\w\\M\\s(?:\\w+\\s){1,2}di\\w*um"]

            :param keywords: A list of strings to search
            :type keywords: list
            :return: list of regular expressions
            :rtype: list
            """
            # Proximity searches have one keyword and contain tilde character
            if len(keywords) == 1 and "~" in keywords[0]:
                # Remove any '"' characters
                kw = keywords[0].replace('"', "")
                # Split keyword around proximity search
                [(fore, prox_op, aft)] = re.findall(r"(.*)\s(~\d?:?\d?)\s(.*)", kw)
                # Fore and aft can be multi-word strings containing wildcards
                # so loop back
                fore = self.transform_keywords_to_regex([fore])
                aft = self.transform_keywords_to_regex([aft])
                [(min_words, isRange, max_words)] = re.findall(
                    r"~(\d)?(:)?(\d)?", prox_op
                )
                min_words = "0" if not min_words else min_words
                if max_words:
                    prox_reg = rf"\s(?:\w+\s){{{min_words},{max_words}}}"
                elif min_words:
                    min_words = min_words + "," if isRange else min_words
                    prox_reg = rf"\s(?:\w+\s){{{min_words}}}"
                else:
                    # Shouldn't happen, just ignore
                    prox_reg = ""
                keywords = ["".join(fore) + prox_reg + "".join(aft)]
            else:
                for i, kw in enumerate(keywords):
                    reg_kw = r"\y"  # \y matches start or end of word
                    for char in kw:
                        if char == WILDCARD_SINGLE_CHAR:
                            reg_kw += (
                                r"\w"  # a single word char (greek chars work here)
                            )
                        elif char == WILDCARD_MANY_CHAR:
                            reg_kw += r"\w*"  # zero or more word characters
                        else:
                            reg_kw += char
                    reg_kw += r"\y"
                    keywords[i] = reg_kw
            return keywords

        def do_match(
            self,
            query_set: QuerySet,
            query_string: str,
            matcher: Callable[[str], Q],
            keyword_list: Iterable[str],
            add_snippet: bool = False,
            weight: int = 1,
        ) -> QuerySet:
            """
            Get the queryset for this match portion.

            :param query_set: The query set to be searched.
            :param query_string: A lookup parameter for the field to be searched.
            :param annotation_name: Arbitrary name for an internal variable.
            :param query: A function that applies the appropriate folding or
              cleaning to the searched field.
            :param matcher: A function taking a lookup string and returning an
              expression for whether the field matches the query.
            :param keywords: The user's query string; a string of keywords.
            :param add_snippet: Should we add a snippet to the resulting queryset?
            :param weight: Weight to annotate the results with.
            :return: The queryset of results and snippets.
            """
            matches = query_set.filter(matcher(f"{query_string}__{self.lookup}"))
            snippet = (
                self.snippet_query(keyword_list, query_string)
                if add_snippet
                else Value("")
            )
            matches = matches.annotate(snippet=snippet, weight=Value(weight))
            return matches

        def snippet_query(self, keyword_list: str, query_string: str) -> Expression:
            """
            Get an expression for a getting a snippet.

            :param keywords: A string of keywords (from the user's query)
            :param query_string: The string for accessing the field.
            :return: An expression for extracting the snippet from the field.
            """
            return Func(
                Func(
                    Func(
                        Func(
                            Func(
                                query_string,
                                Value(self.get_snippet_regex(keyword_list)),
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

        def get_snippet_regex(self, keywords: Iterable[str], before=5, after=5) -> str:
            """
            Get a regular expression that extracts a snippet from text.

            For example we can make an HTML snippet with the Postgres SQL
            ``REGEXP_REPLACE(content, snippet_regex, '\1<span>\2</span>\3')``.

            :param keywords: Iterable of keywords (the user's query) -- they
              have already been split by unquoted space
            :param before: The number of words before a keyword we'd like
              in the snippet.
            :param after: The number of words after a keyword we'd like in the snippet.
            :return: A regex that has three capturing groups: 1 is the previous words,
              2 is the keyword that was matched, 3 is the subsequent words.
            """
            words_before_group = rf"((?:\S+\s){{0,{before}}})"
            keywords_group = "|".join(keywords)
            keywords_group = f"({keywords_group})"
            words_after_group = rf"(.?\s(?:\S+\s){{0,{after}}})"
            snippet_regex = words_before_group + keywords_group + words_after_group
            return snippet_regex

        def match(
            self, query_set: QuerySet, query_string: str, add_snippet: bool = False
        ) -> QuerySet:
            """
            Get the queryset for matching one type of objects, without Latin folding.

            .. code-block:: python

               results = terms.match('foreign_key_1__foreign_key_2__field')

            :param query_set: The query set to be searched.
            :param query_string: A lookup parameter for the field to be searched.
            :param add_snippet: Should we add a snippet to the resulting queryset?
            :return: The queryset of results and snippets. The snippet annotation
              (if present) has the name ``snippet``.
            """
            return self.do_match(
                query_set,
                query_string,
                self.nonfolded_matcher,
                self.keywords,
                add_snippet=add_snippet,
            )

        def match_heavy(
            self, query_set: QuerySet, query_string: str, add_snippet: bool = False
        ) -> QuerySet:
            """
            Get the queryset for matching one type of objects, without Latin folding,
            with extra weight (so they appear at the top of the)

            .. code-block:: python

               results = terms.match('foreign_key_1__foreign_key_2__field')

            :param query_set: The query set to be searched.
            :param query_string: A lookup parameter for the field to be searched.
            :param add_snippet: Should we add a snippet to the resulting queryset?
            :return: The queryset of results and snippets. The snippet annotation
              (if present) has the name ``snippet``.
            """
            return self.do_match(
                query_set,
                query_string,
                self.nonfolded_matcher,
                self.keywords,
                add_snippet=add_snippet,
                weight=100,
            )

        def match_folded(
            self, query_set: QuerySet, query_string: str, add_snippet: bool = False
        ) -> QuerySet:
            """
            Get the queryset for matching one type of objects, with Latin folding.

            .. code-block:: python

              results = terms.match_folded('foreign_key_1__foreign_key_2__field')

            :param query_set: The query set to be searched.
            :param query_string: A lookup parameter for the field to be searched.
            :param add_snippet: Should we add a snippet to the resulting queryset?
            :return: The queryset of results and snippets. The snippet annotation
              (if present) has the name ``snippet``.
            """
            return self.do_match(
                query_set,
                query_string,
                self.folded_matcher,
                self.folded_keywords,
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

        SearchField = tuple[str, str]
        """
        A pair of (lookup string, foldedness); foldedness is "folded" or
        "non-folded". This is used to override the default search fields for
        a particular kind of search.
        """

        search_types: list[SearchField] = [
            ("all content", None),
            ("original texts", ("original_texts__folded_content", "folded")),
            (
                "translations",
                (
                    "original_texts__translation__plain_translated_text",
                    "non-folded",
                ),
            ),
            ("commentary", ("plain_commentary", "non-folded")),
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
    def generic_content_search(
        cls,
        qs: QuerySet,
        search_fields: tuple[str, MatcherCallable],
    ) -> Iterable[Any]:
        """
        Find all the objects that match the query.

        :param qs: The query set to search.
        :param search_fields: All the lookups to perform on the query set,
          and the function to clean or fold the results of these lookups.
        :return: All the objects found.
        """
        results = []
        for field_name, match_function in search_fields:
            matches = match_function(qs, field_name, add_snippet=True)
            results.append(matches)
            # Remove objects from queryset once matched so they don't get matched twice
            qs = qs.exclude(id__in=[o.id for o in matches])
        return chain(*results)

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(
        cls, terms: Term, ant_filter: Iterable[str] | None = None, **kwargs: Any
    ) -> Iterable[Any]:
        """
        Find all the ``Antiquarian``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Antiquarians found.
        """
        qs = cls.get_filtered_model_qs(Antiquarian, ant_filter=ant_filter)
        search_fields = [
            ("name", terms.match_heavy),
            ("plain_introduction", terms.match),
            ("re_code", terms.match_heavy),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def topic_search(cls, terms: Term, **kwargs: Any) -> Iterable[Any]:
        """
        Find all the ``Topic``s that match the query.

        :param term: Object representing the user's query.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Topics found.
        """
        qs = Topic.objects.all()
        search_fields = [("name", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def work_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``Work``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Works found.
        """
        qs = cls.get_filtered_model_qs(Work, ant_filter=ant_filter)
        search_fields = [
            ("name", terms.match),
            ("subtitle", terms.match),
            ("antiquarian__name", terms.match),
            ("plain_introduction", terms.match),
            ("book__plain_introduction", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def book_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``Book``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Books found.
        """
        qs = cls.get_filtered_model_qs(Book, ant_filter=ant_filter)
        search_fields = [
            ("subtitle", terms.match),
            ("work__antiquarian__name", terms.match),
            ("work__name", terms.match),
            ("plain_introduction", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def original_text_owner_search(
        cls,
        terms: Term,
        qs: QuerySet,
        search_field: SearchMethodGroup.SearchField | None = None,
    ) -> Iterable[Any]:
        """
        Find all the ``Fragment``, ``AnonymousFragment`` or ``Testimonium``
        objects that have original texts that match the user's query.

        :param terms: The user's query.
        :param qs: The query set to filter.
        :param search_field: The lookup strings we want to search (and whether
          we want folding for each).
        :return: The objects found.
        """
        if search_field:
            match_function = (
                terms.match_folded if search_field[1] == "folded" else terms.match
            )
            search_fields = [(search_field[0], match_function)]
        else:
            search_fields = [
                ("original_texts__folded_content", terms.match_folded),
                ("original_texts__translation__plain_translated_text", terms.match),
                ("plain_commentary", terms.match),
                ("original_texts__translation__translator_name", terms.match),
                ("original_texts__references__reference_position", terms.match),
                ("original_texts__references__editor", terms.match),
            ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def fragment_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        search_field: SearchMethodGroup.SearchField | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``Fragment``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param ca_filter: A list of citing authors to include in the search.
        :param search_field: The lookup strings we want to search (and whether
          we want folding for each).
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Fragments found.
        """
        qs = cls.get_filtered_model_qs(
            Fragment, ant_filter=ant_filter, ca_filter=ca_filter
        )
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def testimonium_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        search_field: SearchMethodGroup.SearchField | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``Testimonium`` objects that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param ca_filter: A list of citing authors to include in the search.
        :param search_field: The lookup strings we want to search (and whether
          we want folding for each).
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Testimonia found.
        """
        qs = cls.get_filtered_model_qs(
            Testimonium, ant_filter=ant_filter, ca_filter=ca_filter
        )
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def anonymous_fragment_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        search_field: SearchMethodGroup.SearchField | None = None,
        qs: QuerySet | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``AnonymousFragment``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param ca_filter: A list of citing authors to include in the search.
        :param search_field: The lookup strings we want to search (and whether
          we want folding for each).
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Fragments found.
        """
        if not qs:
            qs = cls.get_filtered_model_qs(
                AnonymousFragment, ant_filter=ant_filter, ca_filter=ca_filter
            )
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def appositum_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        search_field: SearchMethodGroup.SearchField | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``AnonymousFragment``s that have associated appositum
          fragments and that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param ca_filter: A list of citing authors to include in the search.
        :param search_field: The lookup strings we want to search (and whether
          we want folding for each).
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Fragments found.
        """
        qs = AnonymousFragment.objects.exclude(appositumfragmentlinks_from=None).all()
        qs = cls.get_filtered_model_qs(
            AnonymousFragment, qs=qs, ant_filter=ant_filter, ca_filter=ca_filter
        )
        return cls.anonymous_fragment_search(
            terms, qs=qs, search_field=search_field, **kwargs
        )

    @classmethod
    def apparatus_criticus_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``Fragment``, ``AnonymousFragment`` or ``Testimonium``
        objects that have apparatus criticus text that match the user's query.

        :param terms: The user's query.
        :param qs: The query set to filter.
        :param search_field: The lookup strings we want to search (and whether
          we want folding for each).
        :return: The objects found.
        """
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
    def bibliography_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``BibliographyItem``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param ca_filter: A list of citing authors to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Bibliographies found.
        """
        qs = cls.get_filtered_model_qs(
            BibliographyItem, ant_filter=ant_filter, ca_filter=ca_filter
        )
        search_fields = [("authors", terms.match), ("title", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def citing_author_search(
        cls,
        terms: Term,
        ca_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[Any]:
        """
        Find all the ``CitingAuthor``s that match the query.

        :param term: Object representing the user's query.
        :param ca_filter: A list of citing authors to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Citing Authors found.
        """
        qs = cls.get_filtered_model_qs(CitingAuthor, ca_filter=ca_filter)
        search_fields = [("name", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def citing_work_search(
        cls, terms: Term, ca_filter: Iterable[str] | None = None, **kwargs
    ) -> Iterable[Any]:
        """
        Find all the ``CitingWork``s that match the query.

        :param term: Object representing the user's query.
        :param ca_filter: A list of citing authors to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Citing Works found.
        """
        qs = cls.get_filtered_model_qs(CitingWork, ca_filter=ca_filter)
        search_fields = [("title", terms.match), ("edition", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def get_filtered_model_qs(
        cls,
        model: type,
        qs: QuerySet | None = None,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
    ) -> QuerySet:
        """
        Get a query set filtered by antiquarian and/or citing author.

        :param model: The type of the queryset results.
        :param qs: The queryset to filter. If None then all objects of
          the ``model`` type are filtered.
        :param ant_filter: List of antiquarians to filter on.
        :param ca_filter: List of citing authors to filter on.
        :return: The filtered query set.
        """
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
                qs = qs.filter(antiquarians__in=ant_filter)
        if ca_filter:
            if model in [Fragment, AnonymousFragment, Testimonium]:
                qs = qs.filter(original_texts__citing_work__author__in=ca_filter)
            if model == CitingWork:
                qs = qs.filter(author__in=ca_filter)
            if model == CitingAuthor:
                qs = qs.filter(id__in=ca_filter)
            if model == BibliographyItem:
                qs = qs.filter(citing_authors__in=ca_filter)
        return qs

    def get(self, request, *args, **kwargs):
        """Perform the search for the user."""
        keywords = request.GET.get("q", None)
        if keywords is not None and keywords.strip() == "":
            # empty search field. Redirect to cleared page
            # Needs to be self.request or github-advanced-security complains
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
            context["bibliographies"],
        ) = self.antiquarians_and_authors_and_bibliographies_in_object_list(
            self.object_list
        )
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
        return sorted(
            queryset_chain,
            key=lambda instance: (instance.weight, instance.pk),
            reverse=True,
        )

    def antiquarians_and_authors_and_bibliographies_in_object_list(self, object_list):
        """Generate lists of Antiquarians, Citing Authors and Bibliographies
        associated with the list of objects provided.

        Antiquarians can come from: Fragments, Testimonia, Anonymous Fragments,
        Antiquarians, or Works.

        Citing Authors can come from: Fragments, Testimonia, Anonymous
        Fragments, Citing Works, or Citing Authors.

        Bibliography items come only from themselves
        """
        antiquarians = []
        authors = []
        bibliographies = []
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
                    bibliographies.append(object)
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
            bibliographies = list(set(bibliographies))
            bibliographies.sort(key=lambda x: x.title)
        else:
            # Return all antiquarians and authors (already sorted)
            antiquarians = list(Antiquarian.objects.all())
            authors = list(CitingAuthor.objects.all())
            bibliographies = list(BibliographyItem.objects.all())
        return antiquarians, authors, bibliographies
