import pytest
from django.contrib.auth.models import Group
from django.test import TestCase

from rard.users.forms import UserCreationForm
from rard.users.models import User
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserCreationForm(TestCase):
    def test_clean_username(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()
        Group.objects.create(name='test')

        form = UserCreationForm(
            {
                "username": proto_user.username,
                "email": 'email@example.com',
                "password1": proto_user._password,
                "password2": proto_user._password,
                'groups': Group.objects.all(),
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.clean_username(), proto_user.username)

        # Creating a user.
        form.save()

        # The user with proto_user params already exists,
        # hence cannot be created.
        form = UserCreationForm(
            {
                "username": proto_user.username,
                "email": 'different_email@example.com',
                "password1": proto_user._password,
                "password2": proto_user._password,
                'groups': Group.objects.all(),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("username", form.errors)

    def test_reserved_username(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()
        Group.objects.create(name='test')

        form = UserCreationForm(
            {
                "username": User.SENTINEL_USERNAME,
                "email": 'email@example.com',
                "password1": proto_user._password,
                "password2": proto_user._password,
                'groups': Group.objects.all(),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("username", form.errors)

    def test_unique_email(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()
        Group.objects.create(name='test')

        form = UserCreationForm(
            {
                "username": 'username',
                "email": proto_user.email,
                "password1": proto_user._password,
                "password2": proto_user._password,
                'groups': Group.objects.all(),
            }
        )

        self.assertTrue(form.is_valid())

        # Create the with this email address
        form.save()

        # The user with this email address already exists,
        # hence cannot be created.
        form = UserCreationForm(
            {
                "username": 'different_username',
                "email": proto_user.email,  # NB same email
                "password1": proto_user._password,
                "password2": proto_user._password,
                'groups': Group.objects.all(),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("email", form.errors)

    def test_groups_required(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        # Try and create a user with no groups and you should
        # raise an error.
        form = UserCreationForm(
            {
                "username": 'different_username',
                "email": proto_user.email,  # NB same email
                "password1": proto_user._password,
                "password2": proto_user._password,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("groups", form.errors)
