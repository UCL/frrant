# from django.contrib.postgres.search import SearchQuery, SearchRank, \
#     SearchVector
from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Value, F, Func
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import ListView, TemplateView

from rard.research.models import (AnonymousFragment, Antiquarian,
                                  BibliographyItem, Fragment, Testimonium,
                                  Topic, Work)
from rard.research.models.citing_work import CitingAuthor, CitingWork

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
['uul', 'vul'],
['uul', 'vol'],
['ui', 'uui'],
['ui', 'uvi'],
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
        def add_fold(self, x, y):
            qu = self.query
            self.query = lambda q: Func(qu(q), Value(x), Value(y), function='replace')

        def __init__(self, keywords):
            self.keywords = keywords
            self.query = lambda x: Lower(x)
            k = keywords.lower()
            for (x, y) in rard_folds:
                if x in k:
                    self.add_fold(y, x)
                elif y in k:
                    k = k.replace(y, x)
                    self.add_fold(y, x)
            self.folded_keywords = k

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
            qs.filter(name__icontains=terms.keywords) |
            qs.filter(introduction__content__icontains=terms.keywords) |
            qs.filter(re_code__icontains=terms.keywords)
        )
        return results.distinct()

    @classmethod
    def topic_search(cls, terms):
        qs = Topic.objects.all()
        results = (
            qs.filter(name__icontains=terms.keywords)
        )
        return results.distinct()

    @classmethod
    def work_search(cls, terms):
        qs = Work.objects.all()
        results = (
            qs.filter(name__icontains=terms.keywords) |
            qs.filter(subtitle__icontains=terms.keywords) |
            qs.filter(antiquarian__name__icontains=terms.keywords)
        )
        return results.distinct()

    @classmethod
    def fragment_search(cls, terms):
        qs = Fragment.objects.all()
        folded_content = qs.annotate(folded=terms.query(F('original_texts__content')))
        folded_commentary = qs.annotate(folded=terms.query(F('commentary__content')))
        results = (
            folded_content.filter(folded__contains=terms.folded_keywords) |
            qs.filter(original_texts__reference__icontains=terms.keywords) |
            qs.filter(original_texts__translation__translated_text__icontains=terms.keywords) |  # noqa
            qs.filter(original_texts__translation__translator_name__icontains=terms.keywords) |  # noqa
            folded_commentary.filter(folded__contains=terms.folded_keywords)
        )
        return results.distinct()

    @classmethod
    def anonymous_fragment_search(cls, terms, qs=None):
        if not qs: qs = AnonymousFragment.objects.all()
        folded_content = qs.annotate(folded=terms.query(F('original_texts__content')))
        folded_commentary = qs.annotate(folded=terms.query(F('commentary__content')))
        results = (
            folded_content.filter(folded__contains=terms.folded_keywords) |
            qs.filter(original_texts__reference__icontains=terms.keywords) |
            qs.filter(original_texts__translation__translated_text__icontains=terms.keywords) |  # noqa
            qs.filter(original_texts__translation__translator_name__icontains=terms.keywords) |  # noqa
            folded_commentary.filter(folded__contains=terms.keywords)
        )
        return results.distinct()

    @classmethod
    def testimonium_search(cls, terms):
        qs = Testimonium.objects.all()
        folded_content = qs.annotate(folded=terms.query(F('original_texts__content')))
        folded_commentary = qs.annotate(folded=terms.query(F('commentary__content')))
        results = (
            folded_content.filter(folded__contains=terms.folded_keywords) |
            qs.filter(original_texts__reference__icontains=terms.keywords) |
            qs.filter(original_texts__translation__translated_text__icontains=terms.keywords) |  # noqa
            qs.filter(original_texts__translation__translator_name__icontains=terms.keywords) |  # noqa
            folded_commentary.filter(folded__contains=terms.keywords)
        )
        return results.distinct()

    @classmethod
    def apparatus_criticus_search(cls, terms):
        query = terms.query(F('original_texts__apparatus_criticus_items__content'))
        qst = Testimonium.objects.all().annotate(folded=query)
        qsa = AnonymousFragment.objects.all().annotate(folded=query)
        qsf = Fragment.objects.all().annotate(folded=query)
        return chain(
            qsf.filter(original_texts__apparatus_criticus_items__content__icontains=terms.keywords).distinct(),  # noqa
            qsa.filter(original_texts__apparatus_criticus_items__content__icontains=terms.keywords).distinct(),  # noqa
            qst.filter(original_texts__apparatus_criticus_items__content__icontains=terms.keywords).distinct()  # noqa
        )

    @classmethod
    def bibliography_search(cls, terms):
        qs = BibliographyItem.objects.all()
        results = (
            qs.filter(authors__icontains=terms.keywords) |
            qs.filter(title__icontains=terms.keywords)
        )
        return results.distinct()

    @classmethod
    def appositum_search(cls, terms):
        qs = AnonymousFragment.objects.exclude(appositumfragmentlinks_from=None).all()
        return cls.anonymous_fragment_search(terms, qs=qs)

    @classmethod
    def citing_author_search(cls, terms):
        qs = CitingAuthor.objects.all()
        return qs.filter(name__icontains=terms.keywords).distinct()

    @classmethod
    def citing_work_search(cls, terms):
        qs = CitingWork.objects.all()
        results = (
            qs.filter(title__icontains=terms.keywords) |
            qs.filter(edition__icontains=terms.keywords)
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
