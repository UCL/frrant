import pytest
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import AnonymousUser
from django.http.response import Http404
from django.test import RequestFactory
from django.urls import reverse

from rard.users.admin import UserAdmin
from rard.users.forms import UserCreationForm
from rard.users.models import User
from rard.users.tests.factories import UserFactory
from rard.users.views import UserUpdateView, user_detail_view

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def test_get_success_url(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_success_url() == f"/users/{user.username}/"

    def test_get_object(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user

    def test_success_message(self, user: User, rf: RequestFactory):
        data = {'first_name': 'New First Name', 'last_name': 'New Last Name'}
        url = reverse('users:detail', kwargs={'username': user.username})
        request = rf.post(url)
        request.user = user
        setattr(request, 'data', data)
        setattr(
            request, '_messages', messages.storage.default_storage(request)
        )
        UserUpdateView.as_view()(request)

        # should have single success message
        storage = messages.get_messages(request)
        assert len(storage) == 1
        for msg in storage:
            assert msg.message == UserUpdateView.SUCCESS_MESSAGE
            assert msg.level == messages.INFO


class TestUserDetailView:
    def test_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = UserFactory()

        response = user_detail_view(request, username=user.username)

        assert response.status_code == 200

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()  # type: ignore

        response = user_detail_view(request, username=user.username)

        assert response.status_code == 302
        assert response.url == "/accounts/login/?next=/fake-url/"

    def test_case_sensitivity(self, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = UserFactory(username="UserName")

        with pytest.raises(Http404):
            user_detail_view(request, username="username")


class TestUserAdminCreateView:

    # Test creation of new user via the admin interface

    def test_admin_create_user(self, user: User, rf: RequestFactory):
        request = rf.get("/admin/")
        request.user = UserFactory()

        site = AdminSite()
        admin = UserAdmin(User, site)

        d = {
            'username': 'jsmith',
            'email': 'jsmith@example.com'
        }
        new_user = User(**d)

        form = UserCreationForm(data=d)
        assert form.is_valid()  # create cleaned_data

        admin.save_model(request, new_user, form, change=False)

        # Though we haven't specified one, the admin sets a useable password
        # so that the user can request a change
        assert user.has_usable_password()
