from uuid import UUID

import pytest

from rard.users.models import User

pytestmark = pytest.mark.django_db


def test_user_display_name():

    # fully specified then full_name should be shown
    d = {
        'first_name': 'John',
        'last_name': 'Smith',
        'username': 'jsmith'
    }
    user = User(**d)
    assert user.display_name() == user.get_full_name()

    # fall back to username where get_full_name returns nothing
    d = {'username': 'jsmith'}
    user = User(**d)
    assert user.display_name() == d['username']


def test_user_primary_key():

    # fully specified then full_name should be shown
    d = {
        'first_name': 'John',
        'last_name': 'Smith',
        'username': 'jsmith'
    }
    user = User(**d)

    # check we are using uuids as primary keys
    assert isinstance(user.pk, UUID)

    # check the reference is correct
    assert user.reference == user.pk.hex[:8]
