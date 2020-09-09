import pytest

from rard.users.forms import UserCreationForm
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserCreationForm:
    def test_clean_username(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = UserCreationForm(
            {
                "username": proto_user.username,
                "email": 'email@example.com',
                "password1": proto_user._password,
                "password2": proto_user._password,
            }
        )

        assert form.is_valid()
        assert form.clean_username() == proto_user.username

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
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors

    def test_unique_email(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build()

        form = UserCreationForm(
            {
                "username": 'username',
                "email": proto_user.email,
                "password1": proto_user._password,
                "password2": proto_user._password,
            }
        )

        assert form.is_valid()

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
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors
