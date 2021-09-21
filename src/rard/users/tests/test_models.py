import pytest
from django.test import TestCase

from rard.users.models import User

pytestmark = pytest.mark.django_db


class TestUser(TestCase):
    def test_user_display_name(self):
        # fully specified then full_name should be shown
        data = {"first_name": "John", "last_name": "Smith", "username": "jsmith"}
        user = User(**data)
        self.assertEqual(user.display_name(), user.get_full_name())

        # fall back to username where get_full_name returns nothing
        data = {"username": "jsmith"}
        user = User(**data)
        self.assertEqual(user.display_name(), data["username"])

    def test_sentinel_user(self):

        user = User.get_sentinel_user()
        self.assertEqual(user.username, User.SENTINEL_USERNAME)
        sentinel_pk = user.pk

        # call it again and insist it's the same object
        user = User.get_sentinel_user()
        self.assertEqual(user.username, User.SENTINEL_USERNAME)
        self.assertEqual(user.pk, sentinel_pk)
