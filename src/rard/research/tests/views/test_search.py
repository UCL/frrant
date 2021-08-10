import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (AnonymousFragment, Antiquarian,
                                  BibliographyItem, CitingWork, Fragment,
                                  Testimonium, TextObjectField, Topic, Work)
from rard.research.models.base import AppositumFragmentLink, FragmentLink
from rard.research.views import SearchView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestSearchView(TestCase):
    def test_login_required(self):
        # remove this test when the site goes public
        url = reverse('search:home')
        request = RequestFactory().get(url)

        # specify an unauthenticated user
        request.user = AnonymousUser()

        response = SearchView.as_view()(
            request,
        )

        # should be redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            '{}?next={}'.format(
                reverse(settings.LOGIN_URL),
                url
            )
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
        Antiquarian.objects.create(name='findme', re_code='1')
        Antiquarian.objects.create(name='andme', re_code='2')

        url = reverse('search:home')
        request = RequestFactory().get(url, data={})
        view.request = request
        self.assertEqual(0, len(view.get_queryset()))

    def test_search_queryset(self):
        view = SearchView()

        # create some data to search
        Antiquarian.objects.create(name='findme', re_code='1')
        Antiquarian.objects.create(name='searchme', re_code='2')
        Work.objects.create(name='hellofromme')

        # search for 'me' in the antiquarians
        data = {
            'what': 'antiquarians',
            'q': 'me',
        }
        url = reverse('search:home')
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(2, len(view.get_queryset()))

        # also test the 'all' parameter
        data = {
            'what': 'all',
            'q': 'me',
        }
        url = reverse('search:home')
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(3, len(view.get_queryset()))

    def test_empty_search_redirects(self):

        # any empty sring should be ignored
        for search_term in ('', ' ', '              '):
            data = {
                'what': 'antiquarians',
                'q': search_term,
            }
            url = reverse('search:home')
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
            'what': 'antiquarians',
            'q': 'hai',
        }
        url = reverse('search:home')
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
            [
                x for x in SearchView().SEARCH_METHODS.keys()
            ],
            [
                'antiquarians',
                'testimonia',
                'anonymous fragments',
                'fragments',
                'topics',
                'works',
                'bibliography',
                'apparatus criticus',
                'apposita',
                'citing author',
                'citing work'
            ]
        )

    def test_search_objects(self):

        view = SearchView()

        # basic tests for antiquarian
        a1 = Antiquarian.objects.create(name='findme', re_code='1')
        a2 = Antiquarian.objects.create(name='foo', re_code='2')
        self.assertEqual(list(view.antiquarian_search('findme')), [a1])
        self.assertEqual(list(view.antiquarian_search('FinDMe')), [a1])
        self.assertEqual(list(view.antiquarian_search('foo')), [a2])
        self.assertEqual(list(view.antiquarian_search('fOo')), [a2])
        self.assertEqual(list(view.antiquarian_search('F')), [a1, a2])

        # topics
        t1 = Topic.objects.create(name='topic', order=1)
        t2 = Topic.objects.create(name='pictures', order=2)
        self.assertEqual(list(view.topic_search('topic')), [t1])
        self.assertEqual(list(view.topic_search('TOPIc')), [t1])
        self.assertEqual(list(view.topic_search('picture')), [t2])
        self.assertEqual(list(view.topic_search('PiCTureS')), [t2])
        self.assertEqual(list(view.topic_search('PIC')), [t1, t2])

        # works
        w1 = Work.objects.create(name='work')
        w2 = Work.objects.create(name='nothing')
        self.assertEqual(list(view.work_search('work')), [w1])
        self.assertEqual(list(view.work_search('WORK')), [w1])
        self.assertEqual(list(view.work_search('nothing')), [w2])
        self.assertEqual(list(view.work_search('NothInG')), [w2])
        self.assertEqual(list(view.work_search('O')), [w2, w1])

        cw = CitingWork.objects.create(title='citing_work')

        # fragments
        f1 = Fragment.objects.create()
        f1.original_texts.create(content='findme', citing_work=cw)

        f2 = Fragment.objects.create()
        f2.original_texts.create(content='notme', citing_work=cw)

        self.assertEqual(list(view.fragment_search('findme')), [f1])
        self.assertEqual(list(view.fragment_search('FINDME')), [f1])
        self.assertEqual(list(view.fragment_search('notme')), [f2])
        self.assertEqual(list(view.fragment_search('NoTMe')), [f2])
        self.assertEqual(list(view.fragment_search('Me')), [f1, f2])

        t1 = Testimonium.objects.create()
        t1.original_texts.create(content='findme', citing_work=cw)

        t2 = Testimonium.objects.create()
        t2.original_texts.create(content='notme', citing_work=cw)

        self.assertEqual(list(view.testimonium_search('findme')), [t1])
        self.assertEqual(list(view.testimonium_search('FINDME')), [t1])
        self.assertEqual(list(view.testimonium_search('notme')), [t2])
        self.assertEqual(list(view.testimonium_search('NoTMe')), [t2])
        self.assertEqual(list(view.testimonium_search('Me')), [t1, t2])

        # fragments with apparatus criticus
        data = {
            'content': 'content',
            'citing_work': cw
        }
        f1 = Fragment.objects.create()
        o1 = f1.original_texts.create(**data)
        o1.apparatus_criticus_items.create(content='stuff')

        t1 = Testimonium.objects.create()
        o2 = t1.original_texts.create(**data)
        o2.apparatus_criticus_items.create(content='nonsense')

        f2 = AnonymousFragment.objects.create()
        o3 = f2.original_texts.create(**data)
        o3.apparatus_criticus_items.create(content='rubbish')

        self.assertEqual(list(view.apparatus_criticus_search('TuF')), [f1])
        self.assertEqual(list(view.apparatus_criticus_search('bBi')), [f2])
        self.assertEqual(list(view.apparatus_criticus_search('nseN')), [t1])
        self.assertEqual(
            list(view.apparatus_criticus_search('s')), [f1, f2, t1]
        )
        self.assertEqual(list(view.apparatus_criticus_search('content')), [])

        # bibliography
        parent = TextObjectField.objects.create(content='foo')
        data = {
            'authors': 'Aab, W',
            'title': 'The Roman Age',
            'parent': parent
        }
        b1 = BibliographyItem.objects.create(**data)
        data = {
            'authors': 'Beeb, Z',
            'title': 'The Roman Era',
            'parent': parent
        }
        b2 = BibliographyItem.objects.create(**data)

        self.assertEqual(list(view.bibliography_search('aab')), [b1])
        self.assertEqual(list(view.bibliography_search('EE')), [b2])
        self.assertEqual(list(view.bibliography_search('romAN')), [b1, b2])

        # anonymous fragments vs. apposita
        data = {
            'content': 'raddish',
            'citing_work': cw
        }
        f1 = Fragment.objects.create()
        af1 = AnonymousFragment.objects.create()
        o1 = af1.original_texts.create(**data)
        af2 = AnonymousFragment.objects.create()
        o2 = af2.original_texts.create(**data)
        # Create appositum link for one of the anonymous fragments
        fl1 = AppositumFragmentLink.objects.create(anonymous_fragment=af1, linked_to=f1)

        self.assertEqual(list(view.anonymous_fragment_search('raddish')), [af1, af2])
        self.assertEqual(list(view.apposita_search('raddish')), [af1])
        

