import pytest
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import AnonymousUser
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.users.admin import UserAdmin
from rard.users.forms import UserCreationForm
from rard.users.models import User
from rard.users.tests.factories import UserFactory
from rard.users.views import UserUpdateView, user_detail_view

pytestmark = pytest.mark.django_db


class TestUserUpdateView(TestCase):
    """
    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.rf = RequestFactory()

    def test_get_success_url(self):
        view = UserUpdateView()
        request = self.rf.get("/fake-url/")
        request.user = self.user

        view.request = request

        self.assertEqual(view.get_success_url(), f"/users/{self.user.username}/")

    def test_get_object(self):
        view = UserUpdateView()
        request = self.rf.get("/fake-url/")
        request.user = self.user

        view.request = request

        self.assertEqual(view.get_object(), self.user)

    def test_success_message(self):
        data = {'first_name': 'New First Name', 'last_name': 'New Last Name'}
        url = reverse('users:detail', kwargs={'username': self.user.username})
        request = self.rf.post(url)
        request.user = self.user
        setattr(request, 'data', data)
        setattr(
            request, '_messages', messages.storage.default_storage(request)
        )
        UserUpdateView.as_view()(request)

        # should have single success message
        storage = messages.get_messages(request)
        self.assertEqual(len(storage), 1)
        for msg in storage:
            self.assertEqual(msg.message, UserUpdateView.SUCCESS_MESSAGE)
            self.assertEqual(msg.level, messages.INFO)


class TestUserDetailView(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.rf = RequestFactory()

    def test_authenticated(self):
        request = self.rf.get("/fake-url/")
        request.user = UserFactory()

        response = user_detail_view(request, username=self.user.username)

        assert response.status_code == 200

    def test_not_authenticated(self):
        request = self.rf.get("/fake-url/")
        request.user = AnonymousUser()  # type: ignore

        response = user_detail_view(request, username=self.user.username)

        assert response.status_code == 302
        assert response.url == "/accounts/login/?next=/fake-url/"

    def test_case_sensitivity(self):
        request = self.rf.get("/fake-url/")
        request.user = UserFactory(username="UserName")

        with pytest.raises(Http404):
            user_detail_view(request, username="username")


class TestUserAdminCreateView(TestCase):

    # Test creation of new user via the admin interface

    def test_admin_create_user(self):
        request = RequestFactory().get("/admin/")
        request.user = UserFactory()

        site = AdminSite()
        admin = UserAdmin(User, site)

        data = {
            'username': 'jsmith',
            'email': 'jsmith@example.com'
        }
        new_user = User(**data)

        form = UserCreationForm(data=data)
        self.assertTrue(form.is_valid())  # create cleaned_data

        admin.save_model(request, new_user, form, change=False)

        # Though we haven't specified one, the admin sets a useable password
        # so that the user can request a change
        refetch = User.objects.get(pk=new_user.pk)
        self.assertTrue(refetch.has_usable_password())
