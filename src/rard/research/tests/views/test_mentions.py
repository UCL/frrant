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
        TestimoniumLink.objects.create(testimonium=self.tt2, antiquarian=self.bixby)

        self.pictures = Topic.objects.create(name="pictures")
        self.coups = Topic.objects.create(name="coups")
        self.estates = Topic.objects.create(name="estates")

        self.andropov = Work.objects.create(name="andropov")
        self.provisions = Work.objects.create(name="provisions")
        self.rose = Work.objects.create(name="rose")

        # create special search items
        self.af11 = AnonymousFragment.objects.create(id=12)
        self.af13 = AnonymousFragment.objects.create(id=14)
        self.af31 = AnonymousFragment.objects.create(id=32)

        self.f1 = Fragment.objects.create()
        FragmentLink.objects.create(fragment=self.f1, antiquarian=self.antman)
        self.f2 = Fragment.objects.create()
        FragmentLink.objects.create(fragment=self.f2, antiquarian=self.andrew)
        self.f3 = Fragment.objects.create()
        FragmentLink.objects.create(fragment=self.f2, antiquarian=self.bixby)

        self.f56 = Fragment.objects.create(id=56)
        self.f523 = Fragment.objects.create(id=523)
        self.f600 = Fragment.objects.create(id=600)

        self.bi1 = BibliographyItem.objects.create(
            authors="fee fie foe",
            author_surnames="Froe",
            title="apples and pears",
            parent=self.antman,
        )
        self.bi2 = BibliographyItem.objects.create(
            authors="tee tie toe",
            author_surnames="Twoe",
            title="peppers and carrots",
            parent=self.andrew,
        )
        self.bi3 = BibliographyItem.objects.create(
            authors="fee fie foe",
            author_surnames="Twoe",
            title="peppers and apples",
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
        Antiquarian.objects.create(name="findme", re_code="1")
        Antiquarian.objects.create(name="andme", re_code="2")

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

    def test_special_search(self):
        view = self.view
        # ideally we could check the relevant function is called

        view.request = self.request(
            data={
                "q": "fr",
            }
        )
        print(list(self.view.get_queryset()))
        # fails because it's including unlinked fsr
        self.assertEqual(3, len(list(view.get_queryset())))

    # def test_search_queryset(self):

    #     # create some data to search
    #     Antiquarian.objects.create(name="andrew", re_code="1")
    #     Antiquarian.objects.create(name="antman", re_code="2")
    #     Work.objects.create(name="andropov")
    #     self.view.request = self.request(
    #         data={
    #             "q": "wk:an",
    #         }
    #     )
    #     self.assertEqual(3, len(self.view.get_queryset()))
    #     self.view.request = self.request(
    #         data={
    #             "q": "aq:andr",
    #         }
    #     )
    #     self.assertEqual(2, len(self.view.get_queryset()))
    #     self.view.request = self.request(
    #         data={
    #             "q": "wk:andre",
    #         }
    #     )
    #     self.assertEqual(1, len(self.view.get_queryset()))
    #     self.view.request = self.request(
    #         data={
    #             "q": "andrei",
    #         }
    #     )
    #     self.assertEqual(0, len(self.view.get_queryset()))

    # def test_search_objects(self):

    #     # basic tests for antiquarian
    #     a1 = Antiquarian.objects.create(name="findme", re_code="1")
    #     a2 = Antiquarian.objects.create(name="foo", re_code="2")
    #     view = self.view
    #     self.assertEqual(list(view.antiquarian_search("findme")), [a1])
    #     self.assertEqual(list(view.antiquarian_search("FinD")), [a1])
    #     self.assertEqual(list(view.antiquarian_search("foo")), [a2])
    #     self.assertEqual(list(view.antiquarian_search("fO")), [a2])
    #     self.assertEqual(list(view.antiquarian_search("F")), [a1, a2])

    #     # topics
    #     t1 = Topic.objects.create(name="topic", order=1)
    #     t2 = Topic.objects.create(name="pictures", order=2)
    #     self.assertEqual(list(view.topic_search("topic")), [t1])
    #     self.assertEqual(list(view.topic_search("TOPIc")), [t1])
    #     self.assertEqual(list(view.topic_search("picture")), [t2])
    #     self.assertEqual(list(view.topic_search("PiCTureS")), [t2])
    #     self.assertEqual(list(view.topic_search("PIC")), [t1, t2])

    #     # works
    #     w1 = Work.objects.create(name="work")
    #     w2 = Work.objects.create(name="nothing")
    #     self.assertEqual(list(view.work_search("work")), [w1])
    #     self.assertEqual(list(view.work_search("WORK")), [w1])
    #     self.assertEqual(list(view.work_search("nothing")), [w2])
    #     self.assertEqual(list(view.work_search("NothInG")), [w2])
    #     self.assertEqual(list(view.work_search("O")), [w2, w1])

    #     # unlinked fragments
    #     f56 = Fragment.objects.create(id=56)
    #     f523 = Fragment.objects.create(id=523)
    #     self.assertEqual(list(view.unlinked_fragment_search("u5")), [f56, f523])

    #     # fragments
    #     f1 = Fragment.objects.create()
    #     FragmentLink.objects.create(fragment=f1, antiquarian=a1)

    #     f2 = Fragment.objects.create()
    #     FragmentLink.objects.create(fragment=f2, antiquarian=a2)

    #     self.assertEqual(list(view.fragment_search("findme")), [f1])
    #     self.assertEqual(list(view.fragment_search("FINDM")), [f1])
    #     self.assertEqual(list(view.fragment_search("foo")), [f2])
    #     self.assertEqual(list(view.fragment_search("Fo")), [f2])
    #     self.assertEqual(list(view.fragment_search("f")), [f1, f2])

    #     t1 = Testimonium.objects.create()
    #     TestimoniumLink.objects.create(testimonium=t1, antiquarian=a1)

    #     t2 = Testimonium.objects.create()
    #     TestimoniumLink.objects.create(testimonium=t2, antiquarian=a2)

    #     self.assertEqual(list(view.testimonium_search("findme")), [t1])
    #     self.assertEqual(list(view.testimonium_search("FIN")), [t1])
    #     self.assertEqual(list(view.testimonium_search("foo")), [t2])
    #     self.assertEqual(list(view.testimonium_search("fO")), [t2])
    #     self.assertEqual(list(view.testimonium_search("F")), [t1, t2])

    #     # anonymous fragments
    #     af1 = AnonymousFragment.objects.create()
    #     AppositumFragmentLink.objects.create(anonymous_fragment=af1, antiquarian=a1)
    #     af2 = AnonymousFragment.objects.create()
    #     AppositumFragmentLink.objects.create(anonymous_fragment=af2, antiquarian=a2)

    #     self.assertEqual(list(view.anonymous_fragment_search("f1")), [af1])
    #     self.assertEqual(list(view.anonymous_fragment_search("F1")), [af1])
    #     self.assertEqual(list(view.anonymous_fragment_search("f2")), [af2])
    #     self.assertEqual(list(view.anonymous_fragment_search("F 2")), [af2])
    #     self.assertEqual(list(view.anonymous_fragment_search("F")), [af1, af2])
    #     self.assertEqual(list(view.anonymous_fragment_search("")), [])
    #     self.assertEqual(list(view.anonymous_fragment_search("1")), [])

    #     # bibliography items
    #     bi1 = BibliographyItem.objects.create(
    #         authors="fee fie foe",
    #         author_surnames="Froe",
    #         title="apples and pears",
    #         parent=a1,
    #     )
    #     bi2 = BibliographyItem.objects.create(
    #         authors="tee tie toe",
    #         author_surnames="Twoe",
    #         title="peppers and carrots",
    #         parent=a2,
    #     )
    #     self.assertEqual(list(view.bibliography_search("fie")), [bi1])
    #     self.assertEqual(list(view.bibliography_search("toe")), [bi2])
    #     self.assertEqual(list(view.bibliography_search("apples")), [bi1])
    #     self.assertEqual(list(view.bibliography_search("and")), [bi1, bi2])
