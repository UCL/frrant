import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    Antiquarian,
    CitingWork,
    Concordance,
    ConcordanceModel,
    Fragment,
    OriginalText,
)
from rard.research.models.base import FragmentLink
from rard.research.models.concordance import Edition, PartIdentifier
from rard.research.views import (
    ConcordanceCreateView,
    ConcordanceDeleteView,
    ConcordanceListView,
    ConcordanceUpdateView,
)
from rard.research.views.concordance import OldConcordanceDeleteView
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
        self.edition = Edition.objects.create(
            name="first_edition", description="description"
        )
        self.identifier_template = PartIdentifier.objects.create(
            edition=self.edition, value="[1-10]"
        )
        self.identifier = PartIdentifier.objects.create(edition=self.edition, value="3")
        self.creation_data = {
            "reference": "55.l",
            "content_type": "F",
            "identifier": self.identifier,
        }
        self.concordance = ConcordanceModel.objects.create(
            **self.creation_data, original_text=self.original_text
        )

    def test_creation_edition_step(self):
        url = reverse("concordance:edition_select")
        data = {
            "edition": self.edition.pk,
            "original_text": self.original_text.pk,
        }

        request = RequestFactory().post(url, data=data)
        request.user = self.user
        response = ConcordanceCreateView.as_view()(request, pk=self.original_text.pk)

        self.assertFalse("id_new_edition" in response.content.decode())
        self.assertTrue("id_new_identifier" in response.content.decode())
        self.assertTrue(f"value={self.edition.pk}" in response.content.decode())

    def test_creation_concordance_step(self):
        url = reverse("concordance:create", kwargs={"pk": self.original_text.pk})
        data = {
            "reference": "55.l",
            "content_type": "F",
            "identifier": self.identifier.pk,
            "edition": self.edition.pk,
        }

        request = RequestFactory().post(url, data=data)
        request.user = self.user
        concordance_count = self.original_text.concordance_models.count()

        response = ConcordanceCreateView.as_view()(request, pk=self.original_text.pk)
        self.original_text.refresh_from_db()
        # check the new concordance is associated with the original text
        self.assertEqual(
            self.original_text.concordance_models.count(), (concordance_count + 1)
        )
        # check it redirects to the owner
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.original_text.owner.pk), response["Location"])

    def test_update_view(self):
        data = {
            "identifier": self.concordance.identifier.pk,
            "reference": "880",
            "content_type": "T",
        }

        url = reverse("concordance:update", kwargs={"pk": self.concordance.pk})

        request = RequestFactory().post(url, data=data)
        request.user = self.user

        response = ConcordanceUpdateView.as_view()(request, pk=self.concordance.pk)
        self.concordance.refresh_from_db()

        # Check that the concordance fields have been updated correctly
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.concordance.reference, "880")
        self.assertEqual(self.concordance.content_type, "T")

    def test_update_success_url(self):
        view = ConcordanceUpdateView()
        request = RequestFactory().get("/")
        request.user = self.user

        view.request = request
        view.object = self.concordance

        self.assertEqual(
            view.get_success_url(), self.original_text.owner.get_absolute_url()
        )

    def test_delete_success_url(self):
        view = ConcordanceDeleteView()
        request = RequestFactory().get("/")
        request.user = self.user

        view.request = request
        view.object = self.concordance

        self.assertEqual(
            view.get_success_url(), self.original_text.owner.get_absolute_url()
        )

    def test_old_delete_success_url(self):
        view = OldConcordanceDeleteView()
        request = RequestFactory().get("/")
        request.user = self.user

        view.request = request
        view.object = Concordance.objects.create(
            source="source",
            identifier="identifier",
            original_text=self.original_text,
        )

        self.assertEqual(
            view.get_success_url(), self.original_text.owner.get_absolute_url()
        )

    def test_post_delete_only(self):
        concordance = self.concordance

        url = reverse("concordance:delete", kwargs={"pk": concordance.pk})
        request = RequestFactory().get(url)
        request.user = self.user
        response = ConcordanceDeleteView.as_view()(request, pk=concordance.pk)
        # deletion via GET not allowed
        self.assertEqual(response.status_code, 405)

    def test_update_context_data(self):
        concordance = self.concordance
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

    def test_antiquarian_search(self):
        # Create a fragment link so something will be returned
        FragmentLink.objects.create(
            fragment=self.fragment, antiquarian=self.antiquarian, order=1
        )
        url = reverse("concordance:list")
        self.client.force_login(self.user)
        response = self.client.post(url, {"antiquarian": self.antiquarian.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn(str(self.fragment.pk), response.content.decode())
        self.assertIn(str(self.concordance), response.content.decode())

    def test_edition_search(self):
        # Create a fragment link so something will be returned
        i2 = PartIdentifier.objects.create(edition=self.edition, value="2")
        ConcordanceModel.objects.create(
            identifier=i2,
            original_text=self.original_text,
            reference="20.u",
            content_type="T",
        )
        url = reverse("concordance:list")
        self.client.force_login(self.user)
        response = self.client.post(url, {"edition": self.edition.pk})
        p3_concordance = ConcordanceModel.objects.get(identifier=self.identifier)
        p2_concordance = ConcordanceModel.objects.get(identifier=i2)
        p3_index = response.content.decode().find(f"{p3_concordance}")
        p2_index = response.content.decode().find(f"{p2_concordance}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content.decode().count(f"{self.edition.name}"), 2
        )  # check two concordances are found
        self.assertTrue(p2_index < p3_index)  # check ordered by identifier

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

        concordance = self.concordance
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
