import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian
from rard.research.views import (AntiquarianCreateView, AntiquarianDeleteView,
                                 AntiquarianDetailView, AntiquarianListView,
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
        antiquarian.lock(request.user)
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
        antiquarian.lock(request.user)

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
        antiquarian.lock(request.user)

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


class TestAntiquarianViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.add_antiquarian',
            AntiquarianCreateView.permission_required
        )
        self.assertIn(
            'research.delete_antiquarian',
            AntiquarianDeleteView.permission_required
        )
        self.assertIn(
            'research.change_antiquarian',
            AntiquarianUpdateView.permission_required
        )
        self.assertIn(
            'research.change_antiquarian',
            AntiquarianWorkCreateView.permission_required
        )
        self.assertIn(
            'research.add_work',
            AntiquarianWorkCreateView.permission_required
        )
        self.assertIn(
            'research.change_antiquarian',
            AntiquarianWorksUpdateView.permission_required
        )
        self.assertIn(
            'research.view_antiquarian',
            AntiquarianListView.permission_required
        )
        self.assertIn(
            'research.view_antiquarian',
            AntiquarianDetailView.permission_required
        )


class TestAntiquarianListView(TestCase):

    def test_context_data_default_ordering_off(self):

        Antiquarian.objects.create()
        order = 'earliest'
        url = reverse('antiquarian:list')
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AntiquarianListView.as_view()(request)

        self.assertIsNone(response.context_data['order'], order)

    def test_context_data_has_ordering(self):

        Antiquarian.objects.create()
        order = 'earliest'
        url = reverse('antiquarian:list') + "?order={}".format(order)
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AntiquarianListView.as_view()(request)

        self.assertEqual(response.context_data['order'], order)

    def test_ordered_queryset(self):
        view = AntiquarianListView()

        # create some data to search
        a1 = Antiquarian.objects.create(
            name='name', re_code='1', order_year=100
        )
        a2 = Antiquarian.objects.create(
            name='name', re_code='2', order_year=500
        )

        # search for 'me' in the antiquarians
        data = {
            'order': 'earliest',
        }
        url = reverse('antiquarian:list')
        request = RequestFactory().get(url, data=data)
        view.request = request
        qs = view.get_queryset()
        self.assertEqual(2, len(qs))
        self.assertEqual([a.pk for a in qs.all()], [a1.pk, a2.pk])

        data = {
            'order': 'latest',
        }
        request = RequestFactory().get(url, data=data)
        view.request = request
        qs = view.get_queryset()
        self.assertEqual(2, len(qs))
        self.assertEqual([a.pk for a in qs.all()], [a2.pk, a1.pk])
