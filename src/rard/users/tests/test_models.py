import pytest

from rard.users.models import User

pytestmark = pytest.mark.django_db


def test_user_display_name():

    # fully specified including 'name' then name should be shown
    d = {
        'name': 'myname',
        'first_name': 'John',
        'last_name': 'Smith',
        'username': 'jsmith'
    }
    user = User(**d)
    assert user.display_name() == d['name']

    # fully specified with no 'name' then full_name should be shown
    d = {
        'first_name': 'John',
        'last_name': 'Smith',
        'username': 'jsmith'
    }
    user = User(**d)
    assert user.display_name() == user.get_full_name()

    # fall back to username where nothing else
    d = {'username': 'jsmith'}
    user = User(**d)
    assert user.display_name() == d['username']
