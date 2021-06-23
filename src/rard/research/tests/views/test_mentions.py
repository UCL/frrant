import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (AnonymousFragment, Antiquarian,
                                  BibliographyItem, CitingWork, Fragment,
                                  Testimonium, TextObjectField, Topic, Work)
from rard.research.models.base import (AppositumFragmentLink, FragmentLink,
                                       TestimoniumLink)
from rard.research.views import MentionSearchView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestMentionsView(TestCase):
    def setUp(self):
        self.url = reverse('search:mention')
        self.view = MentionSearchView()

    def request(self, *args, **kwargs):
        req = RequestFactory().get(self.url, *args, **kwargs)
        req.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return req

    def test_login_required(self):
        request = self.request()

        # specify an unauthenticated user
        request.user = AnonymousUser()

        response = MentionSearchView.as_view()(
            request,
        )

        # should be redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            '{}?next={}'.format(
                reverse(settings.LOGIN_URL),
                self.url
            )
        )
        # but if we have an authenticated user it should work
        request.user = UserFactory()

        response = MentionSearchView.as_view()(
            request,
        )

        self.assertEqual(response.status_code, 200)

    def test_default_queryset(self):
        # if we specify nothing to search, we should get nothing in the
        # search queryset

        # create some data and then show we don't find any of it
        # unless we add search terms to the request
        Antiquarian.objects.create(name='findme', re_code='1')
        Antiquarian.objects.create(name='andme', re_code='2')

        self.view.request = self.request(data={})
        self.assertEqual(0, len(self.view.get_queryset()))

    def test_search_queryset(self):

        # create some data to search
        Antiquarian.objects.create(name='andrew', re_code='1')
        Antiquarian.objects.create(name='antman', re_code='2')
        Work.objects.create(name='andropov')
        self.view.request = self.request(data={
            'q': 'an',
        })
        self.assertEqual(3, len(self.view.get_queryset()))
        self.view.request = self.request(data={
            'q': 'andr',
        })
        self.assertEqual(2, len(self.view.get_queryset()))
        self.view.request = self.request(data={
            'q': 'andre',
        })
        self.assertEqual(1, len(self.view.get_queryset()))
        self.view.request = self.request(data={
            'q': 'andrei',
        })
        self.assertEqual(0, len(self.view.get_queryset()))

    def test_search_objects(self):

        # basic tests for antiquarian
        a1 = Antiquarian.objects.create(name='findme', re_code='1')
        a2 = Antiquarian.objects.create(name='foo', re_code='2')
        view = self.view
        self.assertEqual(list(view.antiquarian_search('findme')), [a1])
        self.assertEqual(list(view.antiquarian_search('FinD')), [a1])
        self.assertEqual(list(view.antiquarian_search('foo')), [a2])
        self.assertEqual(list(view.antiquarian_search('fO')), [a2])
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
        FragmentLink.objects.create(
            fragment=f1,
            antiquarian=a1
        )

        f2 = Fragment.objects.create()
        FragmentLink.objects.create(
            fragment=f2,
            antiquarian=a2
        )

        self.assertEqual(list(view.fragment_search('findme')), [f1])
        self.assertEqual(list(view.fragment_search('FINDM')), [f1])
        self.assertEqual(list(view.fragment_search('foo')), [f2])
        self.assertEqual(list(view.fragment_search('Fo')), [f2])
        self.assertEqual(list(view.fragment_search('f')), [f1, f2])

        t1 = Testimonium.objects.create()
        TestimoniumLink.objects.create(
            testimonium=t1,
            antiquarian=a1
        )

        t2 = Testimonium.objects.create()
        TestimoniumLink.objects.create(
            testimonium=t2,
            antiquarian=a2
        )

        self.assertEqual(list(view.testimonium_search('findme')), [t1])
        self.assertEqual(list(view.testimonium_search('FIN')), [t1])
        self.assertEqual(list(view.testimonium_search('foo')), [t2])
        self.assertEqual(list(view.testimonium_search('fO')), [t2])
        self.assertEqual(list(view.testimonium_search('F')), [t1, t2])

        # anonymous fragments
        af1 = AnonymousFragment.objects.create()
        AppositumFragmentLink.objects.create(
            anonymous_fragment=af1,
            antiquarian=a1
        )
        af2 = AnonymousFragment.objects.create()
        AppositumFragmentLink.objects.create(
            anonymous_fragment=af2,
            antiquarian=a2
        )

        self.assertEqual(list(view.anonymous_fragment_search('f1')), [af1])
        self.assertEqual(list(view.anonymous_fragment_search('F1')), [af1])
        self.assertEqual(list(view.anonymous_fragment_search('f2')), [af2])
        self.assertEqual(list(view.anonymous_fragment_search('F 2')), [af2])
        self.assertEqual(list(view.anonymous_fragment_search('F')), [af1, af2])
        self.assertEqual(list(view.anonymous_fragment_search('')), [])
        self.assertEqual(list(view.anonymous_fragment_search('1')), [])
