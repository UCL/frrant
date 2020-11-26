import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingWork
from rard.research.views import CitingWorkUpdateView, CitingWorkDetailView, CitingWorkDeleteView, CitingAuthorListView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCitingWorkUpdateView(TestCase):

    def test_success_url(self):
        view = CitingWorkUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = CitingWork.objects.create(title='title')

        self.assertEqual(
            view.get_success_url(),
            reverse('citingauthor:work_detail', kwargs={'pk': view.object.pk})
        )


class TestCitingWorkViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.change_citingwork',
            CitingWorkUpdateView.permission_required
        )
        self.assertIn(
            'research.delete_citingwork',
            CitingWorkDeleteView.permission_required
        )
        self.assertIn(
            'research.view_citingwork',
            CitingWorkDetailView.permission_required
        )
        self.assertIn(
            'research.view_citingauthor',
            CitingAuthorListView.permission_required
        )
        self.assertIn(
            'research.view_citingwork',
            CitingAuthorListView.permission_required
        )
