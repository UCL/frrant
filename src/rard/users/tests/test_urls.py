import os

import pytest
from django.test import TestCase
from django.urls import resolve, reverse

from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserProfile(TestCase):
    def test_detail(self):
        prefix = os.environ["URL_PREFIX"]
        user = UserFactory.build()
        self.assertEqual(
            reverse("users:detail", kwargs={"username": user.username}),
            f"/{prefix}users/{user.username}/",
        )
        self.assertEqual(
            resolve(f"/{prefix}users/{user.username}/").view_name, "users:detail"
        )

    def test_update(self):
        prefix = os.environ["URL_PREFIX"]
        self.assertEqual(reverse("users:update"), f"/{prefix}users/update-profile/")
        self.assertEqual(
            resolve(f"/{prefix}users/update-profile/").view_name, "users:update"
        )
