import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Work
from rard.research.views import WorkDeleteView, WorkUpdateView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestWorkSuccessUrls(TestCase):

    def test_update_success_url(self):
        views = [
            WorkUpdateView,
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = UserFactory.create()

            view.request = request
            view.object = Work()

            self.assertEqual(
                view.get_success_url(),
                f"/work/{view.object.pk}/"
            )

    def test_delete_success_url(self):
        view = WorkDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Work()

        self.assertEqual(
            view.get_success_url(),
            reverse('work:list')
        )
