import re
from collections.abc import Callable, Iterable, Sequence
from functools import partial
from string import punctuation
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import (
    Case,
    CharField,
    Expression,
    ExpressionWrapper,
    F,
    Func,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat, Lower, NullIf
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import ListView, TemplateView

from rard.research.models.base import (
    FragmentLink,
    TestimoniumLink
)
from rard.research.models import (
    antiquarian,
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

# Fold [X,Y] transforms all instances of Y into X before matching
# Folds are applied in the specified order, so we don't need
# 'uul' <- 'vul' if we already have 'u' <- 'v'
rard_folds: list[tuple[str, str]] = [
    ("ast", "a est"),
    ("ost", "o est"),
    ("umst", "um est"),
    ("am", "an"),
    ("ausa", "aussa"),
    ("nn", "bn"),
    ("tt", "bt"),
    ("pp", "bp"),
    ("rr", "br"),
    ("ch", "cch"),
    ("clu", "culu"),
    ("claud", "clod"),
    ("has", "hasce"),
    ("his", "hisce"),
    ("hos", "hosce"),
    ("i", "ii"),
    ("i", "j"),
    ("um", "im"),
    ("lagr", "lagl"),
    ("mb", "nb"),
    ("ll", "nl"),
    ("mm", "nm"),
    ("mp", "np"),
    ("mp", "ndup"),
    ("rr", "nr"),
    ("um", "om"),
    ("u", "v"),
    ("u", "y"),
    ("uu", "w"),
    ("ulc", "ulch"),
    ("uul", "uol"),
    ("ui", "uui"),
    ("uum", "uom"),
    ("x", "xs"),
]

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


class ConcatNullable(Func):
    """Concatenate strings with ||. Any NULL argument produces a NULL result."""
    template = "%(expressions)s"
    arg_joiner = " || "


@method_decorator(require_GET, name="dispatch")
class SearchView(LoginRequiredMixin, TemplateView, ListView):
    class Term:
        """
        The keywords for a search, together with the folds and cleaning
        functions relevant to them.
        """

        def __init__(self, keywords: str) -> None:
            """
            Initialize ``Term`` with the keywords.

            :param keywords: The user's query; a string of keywords.
            """
            self.cleaned_number = 1
            self.folded_number = 1
            # Remove all punctuation except wildcard characers
            self.keywords = PUNCTUATION_RE.sub("", keywords).lower()

            # The basic function query function will first eliminate html less than
            # and greater than character codes, then punctuation,
            # and lowercase the 'haystack' strings to be searched.
            self.basic_query: Callable[[str], Expression] = lambda q: Lower(
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
            self.query: Callable[[str], Expression] = self.basic_query
            # Now we call add_fold repeatedly to add more
            # folds to self.query
            k = self.keywords
            # we will add each relevant fold_to -> fold_from replacement
            for fold_to, fold_from in rard_folds:
                # if fold_from is in any of the keywords
                if fold_from in k:
                    # then replace it in the keywords
                    k = k.replace(fold_from, fold_to)
                    # and get it replaced in all the strings searched.
                    self.add_fold(fold_from, fold_to)
                # otherwise if fold_to is in the keywords
                elif fold_to in k:
                    # get it replaced in the strings searched,
                    # but we don't need to replace anything in the keywords.
                    self.add_fold(fold_from, fold_to)
                # otherwise this fold is not relevant
            self.folded_keywords = k
            self.folded_matcher = self.get_matcher(k)
            self.nonfolded_matcher = self.get_matcher(self.keywords)

        def get_matcher(self, keywords: str) -> Callable[[str], Q]:
            """
            Get a matcher for the keyword string.

            :param keywords: The user's input: a string of keywords to search for.
            :return: A function that takes a lookup string and returns an
              expression that matches these keywords in that lookup string.
            """
            keyword_list = self.get_keywords(keywords)
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

        def add_fold(self, fold_from: str, fold_to: str) -> None:
            """
            Add another fold to ``self.query``.

            :param fold_from: The string to find and replace.
            :param fold_to: The replacement string.
            """
            old = self.query
            self.query = lambda q: Func(
                old(q), Value(fold_from), Value(fold_to), function="replace"
            )

        def get_keywords(self, search_string):
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
            # regex 1st alternative matches proximity wil
            keywords = re.findall(
                r"(.+\s~\d?:?\d?\s.+|(?<=\")[^\"]*(?=\")|[^\s\"]+)", search_string
            )
            return self.transform_keywords_to_regex(keywords)

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
            annotation_name: str,
            query: Callable[[str], Q],
            matcher: Callable[[str], Q],
            keywords: str,
            add_snippet: bool = False,
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
            :return: The queryset of results and snippets.
            """
            expression = ExpressionWrapper(
                query(query_string), output_field=TextField()
            )
            annotated = query_set.alias(**{annotation_name: expression})
            matches = annotated.filter(matcher(annotation_name + "__regex"))
            snippet = (
                self.snippet_query(keywords, query_string) if add_snippet else Value("")
            )
            matches = matches.annotate(snippet=snippet)
            return matches

        def snippet_query(self, keywords: str, query_string: str) -> Expression:
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

        def get_snippet_regex(
            self, keywords: str, before: int = 5, after: int = 5
        ) -> str:
            """
            Get a regular expression that extracts a snippet from text.

            For example we can make an HTML snippet with the Postgres SQL
            ``REGEXP_REPLACE(content, snippet_regex, '\1<span>\2</span>\3')``.

            :param keywords: String of keywords (the user's query)
            :param before: The number of words before a keyword we'd like
              in the snippet.
            :param after: The number of words after a keyword we'd like in the snippet.
            :return: A regex that has three capturing groups: 1 is the previous words,
              2 is the keyword that was matched, 3 is the subsequent words.
            """
            keywords = self.get_keywords(keywords)
            words_before_group = rf"((?:\S+\s){{0,{before}}})"
            keywords_group = "|".join(keywords)
            keywords_group = r"(" + keywords_group + r")"
            words_after_group = rf"(.?\s(?:\S+\s){{0,{after}}})"
            snippet_regex = words_before_group + keywords_group + words_after_group
            return snippet_regex

        def match(
            self, query_set: QuerySet, query_string: str, add_snippet: bool = False
        ) -> QuerySet:
            """
            Get the queryset for matching one type of objects, without Latin folding.

            .. code-block:: python

               results = term.match('foreign_key_1__foreign_key_2__field')

            :param query_set: The query set to be searched.
            :param query_string: A lookup parameter for the field to be searched.
            :param add_snippet: Should we add a snippet to the resulting queryset?
            :return: The queryset of results and snippets. The snippet annotation
              (if present) has the name ``snippet``.
            """
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

        def match_folded(
            self, query_set: QuerySet, query_string: str, add_snippet: bool = False
        ) -> QuerySet:
            """
            Get the queryset for matching one type of objects, with Latin folding.

            .. code-block:: python

              results = term.match_folded('foreign_key_1__foreign_key_2__field')

            :param query_set: The query set to be searched.
            :param query_string: A lookup parameter for the field to be searched.
            :param add_snippet: Should we add a snippet to the resulting queryset?
            :return: The queryset of results and snippets. The snippet annotation
              (if present) has the name ``snippet``.
            """
            annotation_name = "folded{0}".format(self.folded_number)
            self.folded_number += 1
            keywords = self.folded_keywords
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

        SearchField = tuple[str, str]
        """
        A pair of (lookup string, foldedness); foldedness is "folded" or
        "non-folded". This is used to override the default search fields for
        a particular kind of search.
        """

        search_types: list[SearchField] = [
            ("all content", None),
            ("original texts", ("original_texts__plain_content", "folded")),
            (
                "translations",
                (
                    "original_texts__translation__plain_translated_text",
                    "non-folded",
                ),
            ),
            ("commentary", ("plain_commentary", "non-folded")),
        ]

        def __init__(self, group_name: str, core_method: Callable[..., QuerySet]) -> None:
            self.group_name = group_name
            self.methods = {
                f"{group_name}_{content_field}": partial(
                    core_method, search_field=search_field
                )
                for content_field, search_field in self.search_types
            }
            self.default_method_name = f"{group_name}_{self.search_types[0][0]}"

        @property
        def default_method(self):
            return {self.default_method_name: self.methods[self.default_method_name]}

        @property
        def display_list(self):
            return [self.group_name] + [type[0] for type in self.search_types]

    @property
    def SEARCH_METHODS(self) -> dict[str, dict[str, Callable[..., QuerySet]]]:
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
        search_fields: Sequence[tuple[str, MatcherCallable]],
    ) -> Iterable[QuerySet]:
        """
        Find all the objects that match the query.

        :param qs: The query set to search.
        :param search_fields: All the lookups to perform on the query set,
          and the function to clean or fold the results of these lookups.
        :return: All the objects found.
        """
        results: list[QuerySet] = [
            match_function(qs, field_name, add_snippet=True)
            for field_name, match_function in search_fields
        ]
        if len(results) <= 1:
            return results
        return [results[0].union(*results[1:])]

    @classmethod
    def annotate_fragment_or_testimonium(cls, qs: QuerySet, name: str, link_type: type, tag: str) -> QuerySet:
        """
        Annotate a queryset returning Fragments or Testimonia with data we need.

        :param name: The name of the model being annotated; "Fragment" or "Testimonium"
        :param link_type: The m2m model between the fragment or testimonium and
          the Work.
        :param tag: The letter used to denote Fragment or Testimonium.
        """
        # All the antiquarians associated with a work, aggregated together
        tag_str = " " + tag
        work_antiquarians = antiquarian.WorkLink.objects.filter(
            work=OuterRef("work")
        ).values("work").annotate(
            ant_names=StringAgg("antiquarian__name", delimiter=", ")
        )
        # All the Testimonium or FragmentLinks that reference a Fragment or Testimonium
        lname = name.lower()
        link_query = link_type.objects.filter(
            **{lname: OuterRef("pk")}
        ).values(lname).annotate(link_name=StringAgg(Case(
            When(work__unknown=False, then=Concat(
                Coalesce(
                    NullIf(Subquery(work_antiquarians.values("ant_names")), Value("")),
                    Value("Anonymous"),
                ),
                Value(": "),
                F("work__name"),
                Value(tag_str),
                Cast(F("work_order") + 1, CharField()),
                Value(" [= "),
                F("antiquarian__name"),
                Value(tag_str),
                Cast(F("order") + 1, CharField()),
                Value("]"),
            )), default=Concat(
                F("antiquarian__name"),
                Value(tag_str),
                Cast(F("order") + 1, CharField()),
            )
        ), delimiter=", "))
        return qs.values(
            class_name=Value(name),
            detail_page=Value(f"{lname}:detail"),
            display_name=Coalesce(
                NullIf(Subquery(link_query.values("link_name")), Value("")),
                Concat(Value("Unlinked "), Cast(F("pk"), CharField())),
            ),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )

    @classmethod
    def annotate_fragment(cls, qs: QuerySet) -> QuerySet:
        """Annotate a queryset returning ``Fragment``s with data we need."""
        return cls.annotate_fragment_or_testimonium(qs, "Fragment", FragmentLink, "F")

    @classmethod
    def annotate_annonymous_fragment(cls, qs: QuerySet) -> QuerySet:
        """Annotate a queryset returning AnonymousFragments with data we need."""
        return qs.values(
            class_name=Value("AnonymousFragment"),
            detail_page=Value("anonymous_fragment:detail"),
            display_name=Concat(
                Value("Anonymous F"),
                Cast(F("order") + 1, CharField()),
            ),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )

    @classmethod
    def annotate_testimonium(cls, qs: QuerySet) -> QuerySet:
        """Annotate a queryset returning Testimonia with the data we need."""
        return cls.annotate_fragment_or_testimonium(qs, "Testimonium", TestimoniumLink, "T")

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(
        cls, terms: Term, ant_filter: Iterable[str] | None = None, **kwargs: Any
    ) -> Iterable[QuerySet]:
        """
        Find all the ``Antiquarian``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Antiquarians found.
        """
        qs = cls.get_filtered_model_qs(Antiquarian, ant_filter=ant_filter).values(
            class_name=Value("Antiquarian"),
            detail_page=Value("antiquarian:detail"),
            display_name=F("name"),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )
        search_fields = [
            ("name", terms.match),
            ("plain_introduction", terms.match),
            ("re_code", terms.match),
        ]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def topic_search(cls, terms: Term, **kwargs: Any) -> Iterable[QuerySet]:
        """
        Find all the ``Topic``s that match the query.

        :param term: Object representing the user's query.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Topics found.
        """
        qs = Topic.objects.all().values(
            class_name=Value("Topic"),
            detail_page=Value("topic:detail"),
            display_name=F("name"),
            key=Value(None, output_field=IntegerField()),
            slug_key=F("slug"),
        )
        search_fields = [("name", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def work_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[QuerySet]:
        """
        Find all the ``Work``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Works found.
        """
        qs = cls.get_filtered_model_qs(Work, ant_filter=ant_filter).values(
            class_name=Value("Work"),
            detail_page=Value("work:detail"),
            display_name=Concat(
                Cast(StringAgg("antiquarian__name", delimiter=", "), CharField()),
                Value(": "),
                F("name"),
            ),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )
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
    ) -> Iterable[QuerySet]:
        """
        Find all the ``Book``s that match the query.

        :param term: Object representing the user's query.
        :param ant_filter: A list of antiquarians to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Books found.
        """
        qs = cls.get_filtered_model_qs(Book, ant_filter=ant_filter).values(
            class_name=Value("Book"),
            detail_page=Value("book:detail"),
            display_name=Coalesce(
                ConcatNullable(Value("Book "), F("number"), Value(": "), F("subtitle")),
                ConcatNullable(Value("Book "), F("number")),
                F("subtitle"),
                output_field=CharField(),
            ),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )
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
    ) -> Iterable[QuerySet]:
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
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        search_field: SearchMethodGroup.SearchField | None = None,
        **kwargs: Any,
    ) -> Iterable[QuerySet]:
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
        qs = cls.annotate_fragment(cls.get_filtered_model_qs(
            Fragment, ant_filter=ant_filter, ca_filter=ca_filter
        ))
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def testimonium_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        search_field: SearchMethodGroup.SearchField | None = None,
        **kwargs: Any,
    ) -> Iterable[QuerySet]:
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
        qs = cls.annotate_testimonium(cls.get_filtered_model_qs(
            Testimonium, ant_filter=ant_filter, ca_filter=ca_filter
        ))
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
    ) -> Iterable[QuerySet]:
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
        if qs is None:
            qs = cls.annotate_annonymous_fragment(cls.get_filtered_model_qs(
                AnonymousFragment, ant_filter=ant_filter, ca_filter=ca_filter
            ))
        return cls.original_text_owner_search(terms, qs, search_field=search_field)

    @classmethod
    def appositum_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        search_field: SearchMethodGroup.SearchField | None = None,
        **kwargs: Any,
    ) -> Iterable[QuerySet]:
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
        qs = cls.annotate_annonymous_fragment(cls.get_filtered_model_qs(
            AnonymousFragment, qs=qs, ant_filter=ant_filter, ca_filter=ca_filter
        ))
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
    ) -> Iterable[QuerySet]:
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
        qst = cls.annotate_testimonium(cls.get_filtered_model_qs(
            Testimonium, ant_filter=ant_filter, ca_filter=ca_filter
        ))
        qsa = cls.annotate_annonymous_fragment(cls.get_filtered_model_qs(
            AnonymousFragment, ant_filter=ant_filter, ca_filter=ca_filter
        ))
        qsf = cls.annotate_fragment(cls.get_filtered_model_qs(
            Fragment, ant_filter=ant_filter, ca_filter=ca_filter
        ))
        return [terms.match_folded(qsf, query_string, add_snippet=True).union(
            terms.match_folded(qsa, query_string, add_snippet=True),
            terms.match_folded(qst, query_string, add_snippet=True),
        )]

    @classmethod
    def bibliography_search(
        cls,
        terms: Term,
        ant_filter: Iterable[str] | None = None,
        ca_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[QuerySet]:
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
        ).values(
            class_name=Value("BibliographyItem"),
            detail_page=Value("bibliography:detail"),
            display_name=Concat(
                F("author_surnames"),
                Coalesce(ConcatNullable(Value(" ["), F("year"), Value("]")), Value("")),
                Value(": "),
                Cast(Func(
                    F("title"),
                    Value(r"\s*<[^>]*>\s*"),
                    Value(" "),
                    Value("g"),
                    function="REGEXP_REPLACE",
                ), output_field=CharField()),
            ),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )
        search_fields = [("authors", terms.match), ("title", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def citing_author_search(
        cls,
        terms: Term,
        ca_filter: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[QuerySet]:
        """
        Find all the ``CitingAuthor``s that match the query.

        :param term: Object representing the user's query.
        :param ca_filter: A list of citing authors to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Citing Authors found.
        """
        qs = cls.get_filtered_model_qs(CitingAuthor, ca_filter=ca_filter).values(
            class_name=Value("CitingAuthor"),
            detail_page=Value("citingauthor:detail"),
            display_name=Coalesce(F("name"), Value("Unnamed Author")),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )
        search_fields = [("name", terms.match)]
        return cls.generic_content_search(qs, search_fields)

    @classmethod
    def citing_work_search(
        cls, terms: Term, ca_filter: Iterable[str] | None = None, **kwargs
    ) -> Iterable[QuerySet]:
        """
        Find all the ``CitingWork``s that match the query.

        :param term: Object representing the user's query.
        :param ca_filter: A list of citing authors to include in the search.
        :param kwargs: Ignored. Here to allow compatibility with other search functions.
        :return: The Citing Works found.
        """
        qs = cls.get_filtered_model_qs(CitingWork, ca_filter=ca_filter).values(
            class_name=Value("CitingWork"),
            detail_page=Value("citingauthor:work_detail"),
            display_name=Concat(
                Coalesce(
                    F("author__name"),
                    Value("Anonymous"),
                    output_field=CharField(),
                ),
                Value(", "),
                F("title"),
            ),
            key=F("id"),
            slug_key=Value(None, output_field=CharField()),
        )
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
        if qs is None:
            qs = model.objects.all()
        if ant_filter:
            if model in [Fragment, Testimonium]:
                qs = qs.filter(linked_antiquarians__in=ant_filter)
            if model == FragmentLink:
                qs = qs.filter(fragment__linked_antiquarians__in=ant_filter)
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
            if model == FragmentLink:
                qs = qs.filter(fragment__original_texts__citing_work__author__in=ca_filter)
            if model == CitingWork:
                qs = qs.filter(author__in=ca_filter)
            if model == CitingAuthor:
                qs = qs.filter(id__in=ca_filter)
            if model == BibliographyItem:
                qs = qs.filter(citing_authors__in=ca_filter)
        return qs

    def get(self, request, *args, **kwargs):
        """Perform the search for the user."""
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

        to_search = self.request.GET.getlist("what", ["all"])
        if to_search == ["all"]:
            # Use default methods rather than all because we don't want
            # to search same fragment several times with different methods
            to_search = self.SEARCH_METHODS["default_methods"].keys()

        result_set = [
            q
            for what in to_search
            for q in self.SEARCH_METHODS["all_methods"][what](terms, **filter_kwargs)
        ]

        if len(result_set) == 0:
            return []
        if len(result_set) == 1:
            return result_set[0]
        return result_set[0].union(*result_set[1:])

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
                # This stuff won't work! Change it to .class_name=="Antiquarian" then find by .key
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
