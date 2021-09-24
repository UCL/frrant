# from django.contrib.postgres.search import SearchQuery, SearchRank, \
#     SearchVector
from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Value, F, Func, Q
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import ListView, TemplateView

from rard.research.models import (AnonymousFragment, Antiquarian,
                                  BibliographyItem, Fragment, Testimonium,
                                  Topic, Work)
from rard.research.models.citing_work import CitingAuthor, CitingWork

# Fold [X,Y] transforms all instances of Y into X before matching
# Folds are applied in the specified order, so we don't need
# 'uul' <- 'vul' if we already have 'u' <- 'v'
rard_folds = [
['ast', 'a est'],
['ost', 'o est'],
['umst', 'um est'],
['am', 'an'],
['ausa', 'aussa'],
['nn', 'bn'],
['tt', 'bt'],
['pp', 'bp'],
['rr', 'br'],
['ch', 'cch'],
['clu', 'culu'],
['claud', 'clod'],
['has', 'hasce'],
['his', 'hisce'],
['hos', 'hosce'],
['i', 'ii'],
['i', 'j'],
['um', 'im'],
['lagr', 'lagl'],
['mb', 'nb'],
['ll', 'nl'],
['mm', 'nm'],
['mp', 'np'],
['mp', 'ndup'],
['rr', 'nr'],
['um', 'om'],
['u', 'v'],
['u', 'y'],
['uu', 'w'],
['ulc', 'ulch'],
['uul', 'uol'],
['ui', 'uui'],
['uum', 'uom'],
['x', 'xs'],
]


@method_decorator(require_GET, name='dispatch')
class SearchView(LoginRequiredMixin, TemplateView, ListView):

    class Term:
        """
        Initialize it with the keywords:
        term = Term(keywords)
        and you get three things:
        original_keywords = term.keywords
        folded_keywords = term.folded_keywords
        query = term.query(F('foreign_key_1__foreign_key_2__field'))
        """

        def __init__(self, keywords):
            self.keywords = keywords
            self.matches_keywords = self.get_matcher(keywords)
            self.query = Lower
            k = keywords.lower()
            for (fold_to, fold_from) in rard_folds:
                if fold_from in k:
                    k = k.replace(fold_from, fold_to)
                    self.add_fold(fold_from, fold_to)
                elif fold_to in k:
                    self.add_fold(fold_from, fold_to)
            self.matches_folded_keywords = self.get_matcher(k)

        def get_matcher(self, keywords):
            keyword_list = self.get_keywords(keywords)
            if len(keyword_list) == 0:
                # want a keyword that will always succeed
                first_keyword = ''
            else:
                first_keyword = keyword_list[0]
                keyword_list = keyword_list[1:]
            matcher = lambda f: Q(**{f: first_keyword})
            for keyword in keyword_list:
                matcher = self.add_keyword(matcher, keyword)
            return matcher

        def add_keyword(self, old, keyword):
            return lambda f: Q(**{f:keyword}) & old(f)

        def add_fold(self, fold_from, fold_to):
            old = self.query
            self.query = lambda q: Func(
                old(q),
                Value(fold_from), Value(fold_to),
                function='replace')

        def get_keywords(self, search_string):
            """
            Turns a string into a series of keywords. This is mostly splittling
            by whitespace, but strings surrounded by double quotes are
            returned verbatim.
            """
            segments = search_string.split('"')
            single_keywords = ' '.join(segments[::2]).split()
            return segments[1::2] + single_keywords


    paginate_by = 10
    template_name = 'research/search_results.html'
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
            'bibliographies': self.bibliography_search,
            'apparatus critici': self.apparatus_criticus_search,
            'apposita': self.appositum_search,
            'citing authors': self.citing_author_search,
            'citing works': self.citing_work_search
        }

    # move to queryset on model managers
    @classmethod
    def antiquarian_search(cls, terms):
        qs = Antiquarian.objects.all()
        results = (
            qs.filter(terms.matches_keywords('name__icontains')) |
            qs.filter(terms.matches_keywords('introduction__content__icontains')) |
            qs.filter(terms.matches_keywords('re_code__icontains'))
        )
        return results.distinct()

    @classmethod
    def topic_search(cls, terms):
        qs = Topic.objects.all()
        results = (
            qs.filter(terms.matches_keywords('name__icontains'))
        )
        return results.distinct()

    @classmethod
    def work_search(cls, terms):
        qs = Work.objects.all()
        results = (
            qs.filter(terms.matches_keywords('name__icontains')) |
            qs.filter(terms.matches_keywords('subtitle__icontains')) |
            qs.filter(terms.matches_keywords('antiquarian__name__icontains'))
        )
        return results.distinct()

    @classmethod
    def fragment_search(cls, terms):
        qs = Fragment.objects.all()
        folded_content = qs.annotate(folded=terms.query(F('original_texts__content')))
        folded_commentary = qs.annotate(folded=terms.query(F('commentary__content')))
        results = (
            folded_content.filter(terms.matches_folded_keywords('folded__contains')) |
            qs.filter(terms.matches_keywords('original_texts__reference__icontains')) |
            qs.filter(terms.matches_keywords('original_texts__translation__translated_text__icontains')) |  # noqa
            qs.filter(terms.matches_keywords('original_texts__translation__translator_name__icontains')) |  # noqa
            folded_commentary.filter(terms.matches_folded_keywords('folded__contains'))
        )
        return results.distinct()

    @classmethod
    def anonymous_fragment_search(cls, terms, qs=None):
        if not qs: qs = AnonymousFragment.objects.all()
        folded_content = qs.annotate(folded=terms.query(F('original_texts__content')))
        folded_commentary = qs.annotate(folded=terms.query(F('commentary__content')))
        results = (
            folded_content.filter(terms.matches_folded_keywords('folded__contains')) |
            qs.filter(terms.matches_keywords('original_texts__reference__icontains')) |
            qs.filter(terms.matches_keywords('original_texts__translation__translated_text__icontains')) |  # noqa
            qs.filter(terms.matches_keywords('original_texts__translation__translator_name__icontains')) |  # noqa
            folded_commentary.filter(terms.matches_folded_keywords('folded__contains'))
        )
        return results.distinct()

    @classmethod
    def testimonium_search(cls, terms):
        qs = Testimonium.objects.all()
        folded_content = qs.annotate(folded=terms.query(F('original_texts__content')))
        folded_commentary = qs.annotate(folded=terms.query(F('commentary__content')))
        results = (
            folded_content.filter(terms.matches_folded_keywords('folded__contains')) |
            qs.filter(terms.matches_keywords('original_texts__reference__icontains')) |
            qs.filter(terms.matches_keywords('original_texts__translation__translated_text__icontains')) |  # noqa
            qs.filter(terms.matches_keywords('original_texts__translation__translator_name__icontains')) |  # noqa
            folded_commentary.filter(terms.matches_folded_keywords('folded__contains'))
        )
        return results.distinct()

    @classmethod
    def apparatus_criticus_search(cls, terms):
        query = terms.query(F('original_texts__apparatus_criticus_items__content'))
        qst = Testimonium.objects.all().annotate(folded=query)
        qsa = AnonymousFragment.objects.all().annotate(folded=query)
        qsf = Fragment.objects.all().annotate(folded=query)
        return chain(
            qsf.filter(terms.matches_folded_keywords('folded__icontains')).distinct(),  # noqa
            qsa.filter(terms.matches_folded_keywords('folded__icontains')).distinct(),  # noqa
            qst.filter(terms.matches_folded_keywords('folded__icontains')).distinct()  # noqa
        )

    @classmethod
    def bibliography_search(cls, terms):
        qs = BibliographyItem.objects.all()
        results = (
            qs.filter(terms.matches_keywords('authors__icontains')) |
            qs.filter(terms.matches_keywords('title__icontains'))
        )
        return results.distinct()

    @classmethod
    def appositum_search(cls, terms):
        qs = AnonymousFragment.objects.exclude(appositumfragmentlinks_from=None).all()
        return cls.anonymous_fragment_search(terms, qs=qs)

    @classmethod
    def citing_author_search(cls, terms):
        qs = CitingAuthor.objects.all()
        return qs.filter(terms.matches_keywords('name__icontains')).distinct()

    @classmethod
    def citing_work_search(cls, terms):
        qs = CitingWork.objects.all()
        results = (
            qs.filter(terms.matches_keywords('title__icontains')) |
            qs.filter(terms.matches_keywords('edition__icontains'))
        )
        return results.distinct()

    def get(self, request, *args, **kwargs):
        keywords = self.request.GET.get('q', None)
        if keywords is not None and keywords.strip() == '':
            # empty search field. Redirect to cleared page
            ret = redirect(self.request.path)
        else:
            ret = super().get(request, *args, **kwargs)

        return ret

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

        terms = SearchView.Term(keywords)

        result_set = []

        to_search = self.request.GET.getlist('what', ['all'])
        if to_search == ['all']:
            to_search = self.SEARCH_METHODS.keys()

        for what in to_search:
            result_set.append(self.SEARCH_METHODS[what](terms))

        queryset_chain = chain(*result_set)

        # return a list...
        return sorted(
            queryset_chain,
            key=lambda instance: instance.pk,
            reverse=True
        )
