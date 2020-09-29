import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian
from rard.research.views import (AntiquarianCreateView, AntiquarianDeleteView,
                                 AntiquarianUpdateView,
                                 AntiquarianWorkCreateView,
                                 AntiquarianWorksUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestAntiquarianSuccessUrls(TestCase):

    def test_get_success_url(self):
        views = [
            AntiquarianCreateView,
            AntiquarianUpdateView,
            AntiquarianWorksUpdateView
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = UserFactory.create()

            view.request = request
            view.object = Antiquarian()

            self.assertEqual(
                view.get_success_url(),
                f"/antiquarian/{view.object.pk}/"
            )

    def test_delete_success_url(self):
        view = AntiquarianDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Antiquarian()

        self.assertEqual(
            view.get_success_url(),
            reverse('antiquarian:list')
        )


class TestAntiquarianWorkCreateView(TestCase):
    # we combine detail view and form mixin
    def test_context_data(self):

        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:create_work',
            kwargs={'pk': antiquarian.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AntiquarianWorkCreateView.as_view()(
            request, pk=antiquarian.pk
        )

        self.assertEqual(
            response.context_data['antiquarian'], antiquarian
        )

    def test_success_url(self):
        view = AntiquarianWorkCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.antiquarian = Antiquarian.objects.create()

        self.assertEqual(
            view.get_success_url(),
            f"/antiquarian/{view.antiquarian.pk}/"
        )

    def test_create(self):

        antiquarian = Antiquarian.objects.create()
        data = {'name': 'name', 'subtitle': 'subtitle'}
        url = reverse(
            'antiquarian:create_work',
            kwargs={'pk': antiquarian.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        AntiquarianWorkCreateView.as_view()(
            request, pk=antiquarian.pk
        )
        self.assertEqual(
            antiquarian.works.count(), 1
        )
        for key, val in data.items():
            self.assertEqual(getattr(antiquarian.works.first(), key), val)

    def test_bad_data(self):
        antiquarian = Antiquarian.objects.create()
        data = {'bad': 'data'}
        url = reverse(
            'antiquarian:create_work',
            kwargs={'pk': antiquarian.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        AntiquarianWorkCreateView.as_view()(
            request, pk=antiquarian.pk
        )
        # no work created
        self.assertEqual(
            antiquarian.works.count(), 0
        )


class TestAntiquarianDeleteView(TestCase):
    def test_post_only(self):

        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:delete',
            kwargs={'pk': antiquarian.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AntiquarianDeleteView.as_view()(
            request, pk=antiquarian.pk
        )
        self.assertEqual(response.status_code, 405)
