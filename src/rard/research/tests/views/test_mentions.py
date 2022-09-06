from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    Fragment,
    Testimonium,
    Topic,
    Work,
)
from rard.research.models.base import FragmentLink, TestimoniumLink
from rard.research.views import MentionSearchView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestMentionsView(TestCase):
    def setUp(self):
        self.url = reverse("search:mention")
        self.view = MentionSearchView()

        # create basic search items
        self.antman = Antiquarian.objects.create(name="antman", re_code="1")
        self.andrew = Antiquarian.objects.create(name="andrew", re_code="2")
        self.bixby = Antiquarian.objects.create(name="bixby", re_code="3")

        self.tt1 = Testimonium.objects.create()
        TestimoniumLink.objects.create(testimonium=self.tt1, antiquarian=self.antman)
        self.tt2 = Testimonium.objects.create()
        TestimoniumLink.objects.create(testimonium=self.tt2, antiquarian=self.andrew)
        self.tt3 = Testimonium.objects.create()
        TestimoniumLink.objects.create(testimonium=self.tt3, antiquarian=self.bixby)

        self.pictures = Topic.objects.create(name="pictures")
        self.coups = Topic.objects.create(name="coups")
        self.estates = Topic.objects.create(name="estates")

        self.andropov = Work.objects.create(name="andropov")
        self.provisions = Work.objects.create(name="provisions")
        self.rose = Work.objects.create(name="rose")

        # create special search items
        self.af13 = AnonymousFragment.objects.create(id=12)
        self.af15 = AnonymousFragment.objects.create(id=14)
        self.af33 = AnonymousFragment.objects.create(id=32)

        self.f1 = Fragment.objects.create()
        FragmentLink.objects.create(fragment=self.f1, antiquarian=self.antman)
        self.f2 = Fragment.objects.create()
        FragmentLink.objects.create(fragment=self.f2, antiquarian=self.andrew)
        self.f3 = Fragment.objects.create()
        FragmentLink.objects.create(fragment=self.f3, antiquarian=self.bixby)

        self.f56 = Fragment.objects.create(id=56)
        self.f523 = Fragment.objects.create(id=523)
        self.f600 = Fragment.objects.create(id=600)

        self.bi1 = BibliographyItem.objects.create(
            authors="fee froe",
            author_surnames="Froe",
            title="apples and pears",
            parent=self.antman,
        )
        self.bi2 = BibliographyItem.objects.create(
            authors="tee twoe",
            author_surnames="Twoe",
            title="peppers and carrots",
            parent=self.andrew,
        )
        self.bi3 = BibliographyItem.objects.create(
            authors="fie froe, tie twoe",
            author_surnames="Froe",
            title="peppers 2 apples",
            parent=self.andrew,
        )

    def request(self, *args, **kwargs):
        req = RequestFactory().get(self.url, *args, **kwargs)
        req.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
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
            response.url, "{}?next={}".format(reverse(settings.LOGIN_URL), self.url)
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
        Antiquarian.objects.create(name="findme", re_code="4")
        Antiquarian.objects.create(name="andme", re_code="5")

        self.view.request = self.request(data={})
        self.assertEqual(0, len(self.view.get_queryset()))

    def test_basic_search(self):
        view = self.view
        # antiquarians
        self.assertEqual(len(list(view.basic_search(view, "aq", ""))), 3)
        self.assertEqual(
            list(view.basic_search(view, "aq", "an")), [self.andrew, self.antman]
        )

        # testimonia
        self.assertEqual(len(list(view.basic_search(view, "tt", ""))), 3)
        self.assertEqual(
            list(view.basic_search(view, "tt", "an")), [self.tt1, self.tt2]
        )

        # topics
        self.assertEqual(len(list(view.basic_search(view, "tp", ""))), 3)
        self.assertEqual(
            list(view.basic_search(view, "tp", "s")),
            [self.pictures, self.coups, self.estates],
        )

        # works
        self.assertEqual(len(list(view.basic_search(view, "wk", ""))), 3)
        self.assertEqual(
            list(view.basic_search(view, "wk", "ro")),
            [self.andropov, self.provisions, self.rose],
        )

    def test_bibliography_search(self):
        view = self.view
        view.request = self.request(
            data={
                "q": "bi",
            }
        )
        # check correct method called
        with mock.patch(
            "rard.research.views.MentionSearchView.bibliography_search"
        ) as mock_search_method:
            view.get_queryset()
            mock_search_method.assert_called_with([])

        # no search term
        self.assertEqual(len(list(view.get_queryset())), 3)

        # number as search: only applicable if number in title
        view.request = self.request(
            data={
                "q": "bi:2",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.bi3)

        # string as search
        view.request = self.request(
            data={
                "q": "bi:fro",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 2)

        # string and number as search, reversible
        view.request = self.request(
            data={
                "q": "bi:froe:2",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.bi3)

        view.request = self.request(
            data={
                "q": "bi:2:two",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.bi3)

    def test_anonymous_fragment_search(self):
        view = self.view
        view.request = self.request(
            data={
                "q": "af",
            }
        )
        # check correct method called
        with mock.patch(
            "rard.research.views.MentionSearchView.anonymous_fragment_search"
        ) as mock_search_method:
            view.get_queryset()
            mock_search_method.assert_called_with([])

        # no search term
        self.assertEqual(len(list(view.get_queryset())), 3)

        # number as search
        view.request = self.request(
            data={
                "q": "af:13",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.af13)

        # string as search: should ignore strings
        view.request = self.request(
            data={
                "q": "af:abc",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 3)

        # string and number as search, reversible
        view.request = self.request(
            data={
                "q": "af:an:13",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.af13)

        view.request = self.request(
            data={
                "q": "af:13:an",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.af13)

    def test_fragment_search(self):
        view = self.view
        view.request = self.request(
            data={
                "q": "fr",
            }
        )
        # check correct method called
        with mock.patch(
            "rard.research.views.MentionSearchView.fragment_search"
        ) as mock_search_method:
            view.get_queryset()
            mock_search_method.assert_called_with([])

        # no search term
        self.assertEqual(len(list(view.get_queryset())), 3)

        # number as search
        view.request = self.request(
            data={
                "q": "fr:1",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 3)

        # string as search
        view.request = self.request(
            data={
                "q": "fr:b",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.f3)

        # string and number as search, reversible
        view.request = self.request(
            data={
                "q": "fr:an:1",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 2)

        view.request = self.request(
            data={
                "q": "fr:1:an",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 2)

    def test_unlinked_fragment_search(self):
        view = self.view
        view.request = self.request(
            data={
                "q": "uf",
            }
        )
        # check correct method called
        with mock.patch(
            "rard.research.views.MentionSearchView.unlinked_fragment_search"
        ) as mock_search_method:
            view.get_queryset()
            mock_search_method.assert_called_with([])

        # no search term
        self.assertEqual(len(list(view.get_queryset())), 3)

        # number as search
        view.request = self.request(
            data={
                "q": "uf:5",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 2)

        # string as search: should ignore strings
        view.request = self.request(
            data={
                "q": "uf:abc",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 3)

        # string and number as search, reversible
        view.request = self.request(
            data={
                "q": "uf:an:6",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.f600)

        view.request = self.request(
            data={
                "q": "uf:6:an",
            }
        )
        self.assertEqual(len(list(view.get_queryset())), 1)
        self.assertEqual(view.get_queryset().first(), self.f600)
