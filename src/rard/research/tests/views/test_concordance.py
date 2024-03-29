import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    CitingWork,
    Concordance,
    Fragment,
    OriginalText,
    Testimonium,
)
from rard.research.models.base import AppositumFragmentLink, FragmentLink
from rard.research.views import (
    ConcordanceCreateView,
    ConcordanceDeleteView,
    ConcordanceListView,
    ConcordanceUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestConcordanceViews(TestCase):
    def setUp(self):
        citing_work = CitingWork.objects.create(title="title")
        self.fragment = Fragment.objects.create(name="name")
        self.antiquarian = Antiquarian.objects.create(name="Romulus", re_code="1")
        self.user = UserFactory.create()
        self.fragment.lock(self.user)
        self.original_text = OriginalText.objects.create(
            owner=self.fragment,
            citing_work=citing_work,
        )

    def test_success_urls(self):
        views = [
            ConcordanceCreateView,
            ConcordanceUpdateView,
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = self.user

            view.request = request
            view.object = Concordance.objects.create(
                original_text=self.original_text,
                source="source",
                identifier="identifier",
            )

            self.assertEqual(
                view.get_success_url(), self.original_text.owner.get_absolute_url()
            )

    def test_delete_success_url(self):
        view = ConcordanceDeleteView()
        request = RequestFactory().get("/")
        request.user = self.user

        view.request = request
        view.object = Concordance.objects.create(
            original_text=self.original_text,
            source="source",
            identifier="identifier",
        )

        self.assertEqual(
            view.get_success_url(), self.original_text.owner.get_absolute_url()
        )

    def test_post_delete_only(self):
        concordance = Concordance.objects.create(
            original_text=self.original_text,
            source="source",
            identifier="identifier",
        )

        url = reverse("concordance:delete", kwargs={"pk": concordance.pk})
        request = RequestFactory().get(url)
        request.user = self.user
        response = ConcordanceDeleteView.as_view()(request, pk=concordance.pk)
        self.assertEqual(response.status_code, 405)

    def test_create_context_data(self):
        url = reverse("concordance:create", kwargs={"pk": self.original_text.pk})
        request = RequestFactory().get(url)
        request.user = self.user
        response = ConcordanceCreateView.as_view()(request, pk=self.original_text.pk)

        self.assertEqual(response.context_data["original_text"], self.original_text)

    def test_create_fails_for_testimonium(self):
        # create an original text for a testimonium
        citing_work = CitingWork.objects.create(title="test")
        testimonium = Testimonium.objects.create(name="name")
        self.user = UserFactory.create()
        testimonium.lock(self.user)
        testimonium_original_text = OriginalText.objects.create(
            owner=testimonium,
            citing_work=citing_work,
        )

        url = reverse("concordance:create", kwargs={"pk": testimonium_original_text.pk})
        request = RequestFactory().get(url)
        request.user = self.user

        # this should be verboten
        with self.assertRaises(Http404):
            ConcordanceCreateView.as_view()(request, pk=testimonium_original_text.pk)

    def test_update_context_data(self):
        concordance = Concordance.objects.create(
            original_text=self.original_text,
            source="source",
            identifier="identifier",
        )
        url = reverse("concordance:update", kwargs={"pk": concordance.pk})
        request = RequestFactory().get(url)
        request.user = self.user
        response = ConcordanceUpdateView.as_view()(request, pk=concordance.pk)

        self.assertEqual(
            response.context_data["original_text"], concordance.original_text
        )

    def test_empty_concordance_list_view(self):
        url = reverse("concordance:list")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_concordance_response_data(self):
        # Create a concordance and fragment link so something will be returned
        Concordance.objects.create(
            original_text=self.original_text,
            source="source",
            identifier="123",
        )
        FragmentLink.objects.create(
            fragment=self.fragment, antiquarian=self.antiquarian, order=1
        )
        url = reverse("concordance:list")
        self.client.force_login(self.user)
        response = self.client.get(url)
        # Check fragment URL
        self.assertEqual(
            response.context["page_obj"][0]["frrant"]["url"],
            self.fragment.get_absolute_url(),
        )
        # Check link display name
        self.assertEqual(
            response.context["page_obj"][0]["frrant"]["display_name"], "Romulus F1"
        )
        # Check concordances
        self.assertEqual(
            response.context["page_obj"][0]["concordances"][0],
            self.original_text.concordances.all()[0],
        )

    def test_multiple_fragment_links_repeat_concordances(self):
        # Create a concordance and fragment link so something will be returned
        Concordance.objects.create(
            original_text=self.original_text,
            source="source",
            identifier="123",
        )
        FragmentLink.objects.create(
            fragment=self.fragment, antiquarian=self.antiquarian, order=1
        )

        # Before...
        url = reverse("concordance:list")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(len(response.context["page_obj"]), 1)

        # Create another fragment link
        antiquarian2 = Antiquarian.objects.create(name="Remus", re_code="2")
        FragmentLink.objects.create(
            fragment=self.fragment, antiquarian=antiquarian2, order=1
        )

        # And after...
        response = self.client.get(url)
        self.assertEqual(len(response.context["page_obj"]), 2)
        # Check new link display name
        self.assertContains(response, "Remus F1")
        # Check concordances
        self.assertEqual(
            response.context["page_obj"][1]["concordances"][0],
            self.original_text.concordances.all()[0],
        )

    def test_anonymous_fragment_concordances_included(self):
        anon_frag = AnonymousFragment.objects.create(name="anonymous fragment")
        ot = OriginalText.objects.create(
            owner=anon_frag,
            citing_work=CitingWork.objects.create(title="work1"),
        )
        Concordance.objects.create(original_text=ot, source="Ketchup", identifier="57")
        AppositumFragmentLink.objects.create(
            anonymous_fragment=anon_frag, antiquarian=self.antiquarian, order=1
        )
        # Check the response
        url = reverse("concordance:list")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(len(response.context["page_obj"]), 1)
        # Check the name
        self.assertContains(response, "Romulus A1")

    def test_create_view_with_original_text(self):
        url = reverse("concordance:create", kwargs={"pk": self.original_text.pk})
        data = {"source": "source", "identifier": "identifier"}

        request = RequestFactory().post(url, data=data)
        request.user = self.user

        # check no concordance previously associated with the original text
        self.assertEqual(self.original_text.concordances.count(), 0)

        ConcordanceCreateView.as_view()(request, pk=self.original_text.pk)

        # check the new concordance is associated with the original text
        self.assertEqual(self.original_text.concordances.count(), 1)

    def test_create_view_dispatch_creates_top_level_object(self):
        # dispatch method creates an attribute used by the
        # locking mechanism so here we ensure it is created
        request = RequestFactory().get("/")
        request.user = self.user
        for view_class in (ConcordanceCreateView,):
            view = view_class()
            view.request = request
            view.kwargs = {"pk": self.original_text.pk}
            view.dispatch(request)
            self.assertEqual(view.top_level_object, self.original_text.owner)

    def test_update_delete_create_top_level_object(self):
        # dispatch method creates an attribute used by the
        # locking mechanism so here we ensure it is created

        concordance = Concordance.objects.create(
            original_text=self.original_text,
            source="source",
            identifier="identifier",
        )
        request = RequestFactory().post("/")
        request.user = self.user

        for view_class in (
            ConcordanceUpdateView,
            ConcordanceDeleteView,
        ):
            view = view_class()
            view.request = request
            view.kwargs = {"pk": concordance.pk}
            view.dispatch(request)
            self.assertEqual(view.top_level_object, self.original_text.owner)


class TestConcordanceViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn(
            "research.add_concordance", ConcordanceCreateView.permission_required
        )
        self.assertIn(
            "research.change_concordance", ConcordanceUpdateView.permission_required
        )
        self.assertIn(
            "research.delete_concordance", ConcordanceDeleteView.permission_required
        )
        self.assertIn(
            "research.view_concordance", ConcordanceListView.permission_required
        )


class TestConcordanceListViewPermissions(TestCase):
    def setUp(self):
        self.user1 = UserFactory()
        self.user2 = UserFactory(is_superuser=False)
        self.view = ConcordanceListView()

    def test_login_required(self):
        # remove this test when the site goes public
        url = reverse("concordance:list")
        request = RequestFactory().get(url)

        # specify an unauthenticated user
        request.user = AnonymousUser()

        self.view.request = request
        response = self.view.dispatch(request)

        # should be redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, "{}?next={}".format(reverse(settings.LOGIN_URL), url)
        )

    def test_exception_if_not_permitted(self):
        request = RequestFactory().get("/")
        request.user = self.user2
        self.view.request = request
        self.assertRaises(PermissionDenied, self.view.dispatch, request)

    def test_access_if_permitted(self):
        request = RequestFactory().get("/")
        request.user = self.user1
        self.view.request = request
        response = self.view.dispatch(request)
        self.assertEqual(response.status_code, 200)
