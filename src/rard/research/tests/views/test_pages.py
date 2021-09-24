import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from rard.research.views import HomeView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestHomeView(TestCase):
    def test_get_home_template_authenticated(self):
        view = HomeView()
        request = RequestFactory().get("/")
        request.user = UserFactory()

        view.request = request

        self.assertIn(
            "research/home.html",
            view.get_template_names(),
        )

    def test_get_home_template_not_authenticated(self):
        view = HomeView()
        request = RequestFactory().get("/")
        request.user = AnonymousUser()  # type: ignore

        view.request = request

        self.assertIn(
            "pages/front.html",
            view.get_template_names(),
        )
