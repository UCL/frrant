import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (Antiquarian, CitingWork, Fragment,
                                  Testimonium, Topic, Work)
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
        # if we have an authenticated user it should work
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

    def test_search_classes(self):
        # the types of objects we can search
        self.assertEqual(
            [
                x for x in SearchView().SEARCH_METHODS.keys()
            ],
            [
                'antiquarians',
                'testimonia',
                'fragments',
                'topics',
                'works',
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
        t1 = Topic.objects.create(name='topic')
        t2 = Topic.objects.create(name='pictures')
        self.assertEqual(list(view.topic_search('topic')), [t1])
        self.assertEqual(list(view.topic_search('TOPIc')), [t1])
        self.assertEqual(list(view.topic_search('picture')), [t2])
        self.assertEqual(list(view.topic_search('PiCTureS')), [t2])
        self.assertEqual(list(view.topic_search('PIC')), [t2, t1])

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
