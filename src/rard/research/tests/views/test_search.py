import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    CitingAuthor,
    CitingWork,
    Fragment,
    Testimonium,
    TextObjectField,
    Topic,
    Work,
)
from rard.research.models.base import AppositumFragmentLink
from rard.research.views import SearchView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestSearchView(TestCase):
    def test_login_required(self):
        # remove this test when the site goes public
        url = reverse("search:home")
        request = RequestFactory().get(url)

        # specify an unauthenticated user
        request.user = AnonymousUser()

        response = SearchView.as_view()(
            request,
        )

        # should be redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, "{}?next={}".format(reverse(settings.LOGIN_URL), url)
        )
        # but if we have an authenticated user it should work
        request.user = UserFactory()

        response = SearchView.as_view()(
            request,
        )

        self.assertEqual(response.status_code, 200)

    def test_default_queryset(self):
        # if we specify nothing to search, we should get nothing in the
        # search queryset
        view = SearchView()

        # create some data and then show we don't find any of it
        # unless we add search terms to the request
        Antiquarian.objects.create(name="findme", re_code="1")
        Antiquarian.objects.create(name="andme", re_code="2")

        url = reverse("search:home")
        request = RequestFactory().get(url, data={})
        view.request = request
        self.assertEqual(0, len(view.get_queryset()))

    def test_search_queryset(self):
        view = SearchView()

        # create some data to search
        Antiquarian.objects.create(name="findme", re_code="1")
        Antiquarian.objects.create(name="searchme", re_code="2")
        Work.objects.create(name="hellofromme")

        # search for 'me' in the antiquarians
        data = {
            "what": "antiquarians",
            "q": "me",
        }
        url = reverse("search:home")
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(2, len(view.get_queryset()))

        # also test the 'all' parameter
        data = {
            "what": "all",
            "q": "me",
        }
        url = reverse("search:home")
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(3, len(view.get_queryset()))

    def test_empty_search_redirects(self):

        # any empty sring should be ignored
        for search_term in ("", " ", "              "):
            data = {
                "what": "antiquarians",
                "q": search_term,
            }
            url = reverse("search:home")
            request = RequestFactory().get(url, data=data)
            request.user = UserFactory()
            view = SearchView()
            view.request = request
            response = SearchView.as_view()(request)

            # check we redirect to the home page without GET params
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, url)

    def test_get_only(self):
        # we only allow GET-based search
        data = {
            "what": "antiquarians",
            "q": "hai",
        }
        url = reverse("search:home")
        # create a POST request instead...
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory()
        view = SearchView()
        view.request = request
        response = SearchView.as_view()(request)

        # verboten
        self.assertEqual(response.status_code, 405)

    def test_search_classes(self):
        # the types of objects we can search
        self.assertEqual(
            [x for x in SearchView().SEARCH_METHODS.keys()],
            [
                "antiquarians",
                "testimonia",
                "anonymous fragments",
                "fragments",
                "topics",
                "works",
                "bibliographies",
                "apparatus critici",
                "apposita",
                "citing authors",
                "citing works",
            ],
        )

    def test_search_objects(self):

        view = SearchView()

        # basic tests for antiquarian
        a1 = Antiquarian.objects.create(name='findme', re_code='1')
        a2 = Antiquarian.objects.create(name='foo', re_code='2')
        self.assertEqual(list(view.antiquarian_search(SearchView.Term('findme'))), [a1])
        self.assertEqual(list(view.antiquarian_search(SearchView.Term('FinDMe'))), [a1])
        self.assertEqual(list(view.antiquarian_search(SearchView.Term('foo'))), [a2])
        self.assertEqual(list(view.antiquarian_search(SearchView.Term('fOo'))), [a2])
        self.assertEqual(list(view.antiquarian_search(SearchView.Term('F'))), [a1, a2])

        # topics
        t1 = Topic.objects.create(name='topic', order=1)
        t2 = Topic.objects.create(name='pictures', order=2)
        self.assertEqual(list(view.topic_search(SearchView.Term('topic'))), [t1])
        self.assertEqual(list(view.topic_search(SearchView.Term('TOPIc'))), [t1])
        self.assertEqual(list(view.topic_search(SearchView.Term('picture'))), [t2])
        self.assertEqual(list(view.topic_search(SearchView.Term('PiCTureS'))), [t2])
        self.assertEqual(list(view.topic_search(SearchView.Term('PIC'))), [t1, t2])

        # works
        w1 = Work.objects.create(name='work')
        w2 = Work.objects.create(name='nothing')
        self.assertEqual(list(view.work_search(SearchView.Term('work'))), [w1])
        self.assertEqual(list(view.work_search(SearchView.Term('WORK'))), [w1])
        self.assertEqual(list(view.work_search(SearchView.Term('nothing'))), [w2])
        self.assertEqual(list(view.work_search(SearchView.Term('NothInG'))), [w2])
        self.assertEqual(list(view.work_search(SearchView.Term('O'))), [w2, w1])

        cw = CitingWork.objects.create(title="citing_work")

        # fragments
        f1 = Fragment.objects.create()
        f1.original_texts.create(
            content='findme with your search powers',
            reference='louisa may alcott',
            citing_work=cw
        )

        f2 = Fragment.objects.create()
        f2.original_texts.create(
            content='not$me',
            reference='daisy ma<>,./?;\'#:@~[]{}-=_+!"£$%^&*()\\|y cooper',
            citing_work=cw
        )

        self.assertEqual(list(view.fragment_search(SearchView.Term('findme yovr'))), [f1])
        self.assertEqual(list(view.fragment_search(SearchView.Term('findme not'))), [])
        self.assertEqual(list(view.fragment_search(SearchView.Term('findme "with yovr" powers'))), [f1])
        self.assertEqual(list(view.fragment_search(SearchView.Term('findme "with yovr powers"'))), [])
        self.assertEqual(list(view.fragment_search(SearchView.Term('FINDME'))), [f1])
        self.assertEqual(list(view.fragment_search(SearchView.Term('notme'))), [f2])
        self.assertEqual(list(view.fragment_search(SearchView.Term('No!TMe'))), [f2])
        self.assertEqual(list(view.fragment_search(SearchView.Term('Me'))), [f1, f2])
        self.assertEqual(list(view.fragment_search(SearchView.Term('may'))), [f1, f2])
        self.assertEqual(list(view.fragment_search(SearchView.Term('m!£$%^&*()_+-=|\\{[}]:;@\'~#<,>.?/ay'))), [f1, f2])
        self.assertEqual(list(view.fragment_search(SearchView.Term('mav'))), [])
        self.assertEqual(list(view.fragment_search(SearchView.Term('alcott "louisa may"'))), [f1])
        self.assertEqual(list(view.fragment_search(SearchView.Term('may "louisa alcott"'))), [])

        f3 = Fragment.objects.create()
        f3.original_texts.create(content='de uita Uaticani', citing_work=cw)

        f4 = Fragment.objects.create()
        f4.original_texts.create(content='vita brevIS', citing_work=cw)

        self.assertEqual(list(view.fragment_search(SearchView.Term('vita'))), [f3, f4])
        self.assertEqual(list(view.fragment_search(SearchView.Term('bREUIs'))), [f4])

        t1 = Testimonium.objects.create()
        t1.original_texts.create(content="findme", citing_work=cw)

        t2 = Testimonium.objects.create()
        t2.original_texts.create(content="notme", citing_work=cw)

        self.assertEqual(list(view.testimonium_search(SearchView.Term('findme'))), [t1])
        self.assertEqual(list(view.testimonium_search(SearchView.Term('FINDME'))), [t1])
        self.assertEqual(list(view.testimonium_search(SearchView.Term('notme'))), [t2])
        self.assertEqual(list(view.testimonium_search(SearchView.Term('NoTMe'))), [t2])
        self.assertEqual(list(view.testimonium_search(SearchView.Term('Me'))), [t1, t2])

        # fragments with apparatus criticus
        data = {"content": "content", "citing_work": cw}
        f1 = Fragment.objects.create()
        o1 = f1.original_texts.create(**data)
        o1.apparatus_criticus_items.create(content="stuff")

        t1 = Testimonium.objects.create()
        o2 = t1.original_texts.create(**data)
        o2.apparatus_criticus_items.create(content="nonsense")

        f2 = AnonymousFragment.objects.create()
        o3 = f2.original_texts.create(**data)
        o3.apparatus_criticus_items.create(content="rubbish")

        self.assertEqual(list(view.apparatus_criticus_search(SearchView.Term('TuF'))), [f1])
        self.assertEqual(list(view.apparatus_criticus_search(SearchView.Term('TVF'))), [f1])
        self.assertEqual(list(view.apparatus_criticus_search(SearchView.Term('bBi'))), [f2])
        self.assertEqual(list(view.apparatus_criticus_search(SearchView.Term('nseN'))), [t1])
        self.assertEqual(
            list(view.apparatus_criticus_search(SearchView.Term('s'))), [f1, f2, t1]
        )
        self.assertEqual(list(view.apparatus_criticus_search(SearchView.Term('content'))), [])

        # bibliography
        parent = TextObjectField.objects.create(content="foo")
        data = {"authors": "Aab, W", "title": "The Roman Age", "parent": parent}
        b1 = BibliographyItem.objects.create(**data)
        data = {"authors": "Beeb, Z", "title": "The Roman Era", "parent": parent}
        b2 = BibliographyItem.objects.create(**data)

        self.assertEqual(list(view.bibliography_search(SearchView.Term('aab'))), [b1])
        self.assertEqual(list(view.bibliography_search(SearchView.Term('EE'))), [b2])
        self.assertEqual(list(view.bibliography_search(SearchView.Term('romAN'))), [b1, b2])

        # anonymous fragments vs. apposita
        data = {"content": "raddish", "citing_work": cw}
        f1 = Fragment.objects.create()
        af1 = AnonymousFragment.objects.create()
        o1 = af1.original_texts.create(**data)
        af2 = AnonymousFragment.objects.create()
        o2 = af2.original_texts.create(**data)
        # Create appositum link for one of the anonymous fragments
        AppositumFragmentLink.objects.create(anonymous_fragment=af1, linked_to=f1)

        self.assertEqual(list(view.anonymous_fragment_search(SearchView.Term('raddish'))), [af1, af2])
        self.assertEqual(list(view.appositum_search(SearchView.Term('raddish'))), [af1])

        # citing authors
        ca1 = CitingAuthor.objects.create(name="Alice")
        ca2 = CitingAuthor.objects.create(name="Felicity")

        self.assertEqual(list(view.citing_author_search(SearchView.Term('al'))), [ca1])
        self.assertEqual(list(view.citing_author_search(SearchView.Term('fe'))), [ca2])
        self.assertEqual(list(view.citing_author_search(SearchView.Term('lic'))), [ca1, ca2])

        # citing works
        cw1 = CitingWork.objects.create(title='Opus',edition='Book one',author=ca1)
        cw2 = CitingWork.objects.create(title='Book',edition='Sixth',author=ca2)

        self.assertEqual(list(view.citing_work_search(SearchView.Term('opu'))), [cw1])
        self.assertEqual(list(view.citing_work_search(SearchView.Term('xth'))), [cw2])
        self.assertEqual(list(view.citing_work_search(SearchView.Term('ook'))), [cw1, cw2])
        

        self.assertEqual(list(view.citing_work_search(SearchView.Term("opu"))), [cw1])
        self.assertEqual(list(view.citing_work_search(SearchView.Term("xth"))), [cw2])
        self.assertEqual(list(view.citing_work_search(SearchView.Term("ook"))), [cw1, cw2])
