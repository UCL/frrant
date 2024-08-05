import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian
from rard.research.views import (
    AntiquarianCreateView,
    AntiquarianDeleteView,
    AntiquarianDetailView,
    AntiquarianListView,
    AntiquarianUpdateIntroductionView,
    AntiquarianUpdateView,
    AntiquarianWorkCreateView,
    AntiquarianWorksUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestAntiquarianSuccessUrls(TestCase):
    def test_get_success_url(self):
        views = [
            AntiquarianCreateView,
            AntiquarianUpdateView,
            AntiquarianWorksUpdateView,
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = UserFactory.create()

            view.request = request
            view.object = Antiquarian()

            self.assertEqual(view.get_success_url(), f"/antiquarian/{view.object.pk}/")

    def test_delete_success_url(self):
        view = AntiquarianDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Antiquarian()

        self.assertEqual(view.get_success_url(), reverse("antiquarian:list"))


class TestAntiquarianWorkCreateView(TestCase):
    # we combine detail view and form mixin
    def test_context_data(self):
        antiquarian = Antiquarian.objects.create()
        url = reverse("antiquarian:create_work", kwargs={"pk": antiquarian.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        antiquarian.lock(request.user)
        response = AntiquarianWorkCreateView.as_view()(request, pk=antiquarian.pk)

        self.assertEqual(response.context_data["antiquarian"], antiquarian)

    def test_success_url(self):
        view = AntiquarianWorkCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.antiquarian = Antiquarian.objects.create()

        self.assertEqual(view.get_success_url(), f"/antiquarian/{view.antiquarian.pk}/")

    def test_create(self):
        antiquarian = Antiquarian.objects.create()
        data = {"name": "name", "subtitle": "subtitle"}
        url = reverse("antiquarian:create_work", kwargs={"pk": antiquarian.pk})

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()
        antiquarian.lock(request.user)

        AntiquarianWorkCreateView.as_view()(request, pk=antiquarian.pk)
        self.assertEqual(antiquarian.works.exclude(unknown=True).count(), 1)
        for key, val in data.items():
            self.assertEqual(getattr(antiquarian.works.first(), key), val)

    def test_bad_data(self):
        antiquarian = Antiquarian.objects.create()
        data = {"bad": "data"}
        url = reverse("antiquarian:create_work", kwargs={"pk": antiquarian.pk})

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()
        antiquarian.lock(request.user)

        AntiquarianWorkCreateView.as_view()(request, pk=antiquarian.pk)
        # no work created
        self.assertEqual(antiquarian.works.exclude(unknown=True).count(), 0)


class TestAntiquarianDeleteView(TestCase):
    def test_post_only(self):
        antiquarian = Antiquarian.objects.create()
        url = reverse("antiquarian:delete", kwargs={"pk": antiquarian.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AntiquarianDeleteView.as_view()(request, pk=antiquarian.pk)
        self.assertEqual(response.status_code, 405)


class TestAntiquarianViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn(
            "research.add_antiquarian", AntiquarianCreateView.permission_required
        )
        self.assertIn(
            "research.delete_antiquarian", AntiquarianDeleteView.permission_required
        )
        self.assertIn(
            "research.change_antiquarian", AntiquarianUpdateView.permission_required
        )
        self.assertIn(
            "research.change_antiquarian", AntiquarianWorkCreateView.permission_required
        )
        self.assertIn(
            "research.add_work", AntiquarianWorkCreateView.permission_required
        )
        self.assertIn(
            "research.change_antiquarian",
            AntiquarianWorksUpdateView.permission_required,
        )
        self.assertIn(
            "research.view_antiquarian", AntiquarianListView.permission_required
        )
        self.assertIn(
            "research.view_antiquarian", AntiquarianDetailView.permission_required
        )


class TestAntiquarianListView(TestCase):
    def test_context_data_default_ordering_off(self):
        Antiquarian.objects.create()
        order = "earliest"
        url = reverse("antiquarian:list")
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AntiquarianListView.as_view()(request)

        self.assertIsNone(response.context_data["order"], order)

    def test_context_data_has_ordering(self):
        Antiquarian.objects.create()
        order = "earliest"
        url = reverse("antiquarian:list") + "?order={}".format(order)
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AntiquarianListView.as_view()(request)

        self.assertEqual(response.context_data["order"], order)

    def test_ordered_queryset(self):
        view = AntiquarianListView()

        # create some data to search
        a1 = Antiquarian.objects.create(name="name", re_code="1", order_year=100)
        a2 = Antiquarian.objects.create(name="name", re_code="2", order_year=500)

        # search for 'me' in the antiquarians
        data = {
            "order": "earliest",
        }
        url = reverse("antiquarian:list")
        request = RequestFactory().get(url, data=data)
        view.request = request
        qs = view.get_queryset()
        self.assertEqual(2, len(qs))
        self.assertEqual([a.pk for a in qs.all()], [a1.pk, a2.pk])

        data = {
            "order": "latest",
        }
        request = RequestFactory().get(url, data=data)
        view.request = request
        qs = view.get_queryset()
        self.assertEqual(2, len(qs))
        self.assertEqual([a.pk for a in qs.all()], [a2.pk, a1.pk])


class TestAntiquarianUpdateIntroductionView(TestCase):
    def setUp(self):
        self.antiquarian = Antiquarian.objects.create()
        self.url = reverse(
            "antiquarian:update_introduction", kwargs={"pk": self.antiquarian.pk}
        )
        self.request = RequestFactory().get(self.url)
        self.request.user = UserFactory.create()

        self.antiquarian.lock(self.request.user)
        self.response = AntiquarianUpdateIntroductionView.as_view()(
            self.request, pk=self.antiquarian.pk
        )

    def test_context_data(self):
        self.assertEqual(
            self.response.context_data["text_object"], self.antiquarian.introduction
        )
        self.assertEqual(self.response.context_data["object_class"], "antiquarian")

    def test_success_url(self):
        # this is more complicated than with other views
        # due to the conditional rendering on another view
        # // I think
        success_url = self.response.context_data["view"].get_success_url()
        self.assertEqual(success_url, f"/antiquarian/{self.antiquarian.pk}/")

    def test_update_intro(self):
        """This checks that an introduction object is created
        when the book object is created but is empty
        and will update on POST"""
        intro = self.response.context_data["object"].introduction

        self.assertTrue(bool(intro.pk))
        self.assertFalse(bool(intro.content))

        ant_pk = self.response.context_data["object"].pk

        intro_text = "testing update of introduction"

        data = {
            "introduction_text": intro_text,
        }
        post_request = RequestFactory().post(self.url, data=data)
        post_request.user = self.request.user
        AntiquarianUpdateIntroductionView.as_view()(post_request, pk=ant_pk)

        self.antiquarian.refresh_from_db()
        intro = self.antiquarian.introduction
        self.assertTrue(bool(intro.content))
        self.assertEqual(intro.content, intro_text)
