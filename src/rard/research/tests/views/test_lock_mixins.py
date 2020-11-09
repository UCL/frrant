from datetime import timedelta

import pytest
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from rard.research.models import Antiquarian
from rard.research.views import (AntiquarianDetailView,
                                 AntiquarianWorkCreateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCheckLockMixin(TestCase):

    def test_edit_needs_lock(self):
        antiquarian = Antiquarian.objects.create()
        data = {'name': 'name', 'subtitle': 'subtitle'}
        url = reverse(
            'antiquarian:create_work',
            kwargs={'pk': antiquarian.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        # Do Not Lock the Antiquarian...
        # antiquarian.lock(request.user)

        response = AntiquarianWorkCreateView.as_view()(
            request, pk=antiquarian.pk
        )
        # check we were redirected to the 'no lock' page
        response_content = response.content.decode('utf-8')
        self.assertTrue(response_content.find('😢') > 0)


class TestCanLockMixin(TestCase):

    def test_post_creates_lock(self):
        # choose the AntiquarianDetailView for this
        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:detail',
            kwargs={'pk': antiquarian.pk}
        )
        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'lock': ''  # NB we clicked the lock button
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        # call the view
        AntiquarianDetailView.as_view()(
            request, pk=antiquarian.pk
        )

        # ensure the user has the lock
        refetch = Antiquarian.objects.get(pk=antiquarian.pk)
        self.assertTrue(refetch.is_locked())
        self.assertEqual(refetch.locked_by, request.user)

    def test_post_unlocks(self):
        # choose the AntiquarianDetailView for this
        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:detail',
            kwargs={'pk': antiquarian.pk}
        )
        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'unlock': ''  # NB we clicked the unlock button
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        antiquarian.lock(request.user)
        self.assertTrue(antiquarian.is_locked())

        # call the view
        AntiquarianDetailView.as_view()(
            request, pk=antiquarian.pk
        )

        # ensure the user no longer has the lock
        refetch = Antiquarian.objects.get(pk=antiquarian.pk)
        self.assertFalse(refetch.is_locked())
        self.assertIsNone(refetch.locked_by)

    def test_post_fails_if_locked(self):
        # choose the AntiquarianDetailView for this
        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:detail',
            kwargs={'pk': antiquarian.pk}
        )
        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'lock': ''  # NB we clicked the lock button
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        # hold on, another user has the lock
        another_user = UserFactory.create()
        antiquarian.lock(another_user)

        # call the view
        response = AntiquarianDetailView.as_view()(
            request, pk=antiquarian.pk
        )

        # ensure we were redirected to the 'sorry' page
        response_content = response.content.decode('utf-8')
        self.assertTrue(response_content.find('😢') > 0)

        # ensure the other user still has the lock
        refetch = Antiquarian.objects.get(pk=antiquarian.pk)
        self.assertTrue(refetch.is_locked())
        self.assertEqual(refetch.locked_by, another_user)

    def test_post_requests_lock(self):
        # choose the AntiquarianDetailView for this
        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:detail',
            kwargs={'pk': antiquarian.pk}
        )
        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'request': ''  # NB we clicked the request lock button
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        # another user has the lock
        another_user = UserFactory.create()
        antiquarian.lock(another_user)

        # call the view
        AntiquarianDetailView.as_view()(
            request, pk=antiquarian.pk
        )

        # ensure we have a request for a lock for the user
        self.assertEqual(request.user.objectlockrequest_set.count(), 1)

        # check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [another_user.email])
        self.assertEqual(mail.outbox[0].subject, 'Request to edit record')

    def test_post_break_lock(self):
        # one user has the lock
        antiquarian = Antiquarian.objects.create()
        locking_user = UserFactory.create()
        antiquarian.lock(locking_user)
        self.assertTrue(antiquarian.is_locked())
        self.assertEqual(antiquarian.locked_by, locking_user)

        url = reverse(
            'antiquarian:detail',
            kwargs={'pk': antiquarian.pk}
        )
        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'break': ''  # NB we clicked the break button
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()  # another user tried to break lock

        # test the 'should fail' case first:
        request.user.can_break_locks = False

        # call the view
        AntiquarianDetailView.as_view()(
            request, pk=antiquarian.pk
        )

        # ensure the user still has the lock
        refetch = Antiquarian.objects.get(pk=antiquarian.pk)
        self.assertTrue(refetch.is_locked())

        # now grant the user permission to break locks
        request.user.can_break_locks = True

        # call the view
        AntiquarianDetailView.as_view()(
            request, pk=antiquarian.pk
        )

        # ensure the lock is now broken
        refetch = Antiquarian.objects.get(pk=antiquarian.pk)
        self.assertFalse(refetch.is_locked())
        self.assertIsNone(refetch.locked_by)

    def test_post_lock_until(self):
        # choose the AntiquarianDetailView for this
        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:detail',
            kwargs={'pk': antiquarian.pk}
        )
        DAYS = 5

        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'days': 5
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        time_before = timezone.now()

        # call the view
        AntiquarianDetailView.as_view()(
            request, pk=antiquarian.pk
        )

        time_after = timezone.now()

        # ensure the user has the lock
        refetch = Antiquarian.objects.get(pk=antiquarian.pk)
        self.assertTrue(refetch.is_locked())
        self.assertTrue(
            time_before + timedelta(days=DAYS) <
            refetch.locked_until <
            time_after + timedelta(days=DAYS)
        )
