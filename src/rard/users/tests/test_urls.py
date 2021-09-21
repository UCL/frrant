import pytest
from django.test import TestCase
from django.urls import resolve, reverse

from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserProfile(TestCase):
    def test_detail(self):
        user = UserFactory.build()
        self.assertEqual(
            reverse("users:detail", kwargs={"username": user.username}),
            f"/users/{user.username}/",
        )
        self.assertEqual(resolve(f"/users/{user.username}/").view_name, "users:detail")

    def test_update(self):
        self.assertEqual(reverse("users:update"), "/users/update-profile/")
        self.assertEqual(resolve("/users/update-profile/").view_name, "users:update")
