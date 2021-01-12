import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, Work
from rard.research.views import (WorkCreateView, WorkDeleteView,
                                 WorkDetailView, WorkListView, WorkUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestWorkSuccessUrls(TestCase):

    def test_update_success_url(self):
        views = [
            WorkUpdateView,
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = UserFactory.create()

            view.request = request
            view.object = Work()

            self.assertEqual(
                view.get_success_url(),
                f"/work/{view.object.pk}/"
            )

    def test_delete_success_url(self):
        view = WorkDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Work()

        self.assertEqual(
            view.get_success_url(),
            reverse('work:list')
        )


class TestWorkDeleteView(TestCase):
    def test_post_only(self):

        work = Work.objects.create(name='name')
        url = reverse(
            'work:delete',
            kwargs={'pk': work.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = WorkDeleteView.as_view()(
            request, pk=work.pk
        )
        self.assertEqual(response.status_code, 405)


class TestWorkViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.add_work',
            WorkCreateView.permission_required
        )
        self.assertIn(
            'research.delete_work',
            WorkDeleteView.permission_required
        )
        self.assertIn(
            'research.change_work',
            WorkUpdateView.permission_required
        )
        self.assertIn(
            'research.view_work',
            WorkListView.permission_required
        )
        self.assertIn(
            'research.view_work',
            WorkDetailView.permission_required
        )


class TestWorkCreateView(TestCase):

    def test_create(self):

        url = reverse(
            'work:create'
        )
        a = Antiquarian.objects.create(name='foo', re_code=1)
        data = {'antiquarians': [a.pk], 'name': 'work name'}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        WorkCreateView.as_view()(
            request
        )
        a = Antiquarian.objects.get(pk=a.pk)
        self.assertEqual(
            a.works.count(), 1
        )


class TestWorkUpdateView(TestCase):

    def test_update(self):

        work = Work.objects.create(name='name')
        url = reverse(
            'work:update',
            kwargs={'pk': work.pk}
        )
        a1 = Antiquarian.objects.create(name='foo', re_code=1)
        a2 = Antiquarian.objects.create(name='foo', re_code=2)

        data = {'antiquarians': [a1.pk], 'name': 'first'}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        work.lock(request.user)

        WorkUpdateView.as_view()(
            request, pk=work.pk
        )
        self.assertEqual(
            a1.works.count(), 1
        )
        self.assertEqual(
            a2.works.count(), 0
        )
        self.assertEqual(
            Work.objects.get(pk=work.pk).name, 'first'
        )

        work = Work.objects.create(name='name')
        work.antiquarian_set.add(a1)

        # now transfer this work to another
        data = {'antiquarians': [a2.pk], 'name': 'other'}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        work.lock(request.user)

        view = WorkUpdateView.as_view()
        # view.form.instance = work

        view(
            request, pk=work.pk
        )
        self.assertEqual(
            a1.works.count(), 1
        )
        self.assertEqual(
            a2.works.count(), 1
        )
        self.assertEqual(
            Work.objects.get(pk=work.pk).name, 'other'
        )
