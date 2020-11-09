import pytest
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from rard.research.models import Antiquarian
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestLocks(TestCase):

    def setUp(self):
        data = {
            'name': 'John Smith',
            're_code': 'smitre001'
        }
        self.antiquarian = Antiquarian.objects.create(**data)
        self.user = UserFactory.create()

    def test_default_unlocked(self):
        self.assertFalse(self.antiquarian.is_locked())

    def test_lock(self):
        self.antiquarian.lock(self.user)
        self.assertTrue(self.antiquarian.is_locked())

    def test_unlock(self):
        self.antiquarian.lock(self.user)
        self.antiquarian.unlock()
        self.assertFalse(self.antiquarian.is_locked())
        self.assertIsNone(self.antiquarian.locked_at)

    def test_unlock_with_requests(self):
        self.antiquarian.lock(self.user)
        other_user = UserFactory.create()
        self.antiquarian.request_lock(other_user)
        self.antiquarian.unlock()
        # the requester should be emailed. We should have two emails
        # one for the lock request, the other for the unlock event
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].to, [other_user.email])
        self.assertEqual(
            mail.outbox[1].subject,
            'The item you requested has become available'
        )

    def test_locked_at(self):
        # default none
        self.assertIsNone(self.antiquarian.locked_at)
        before = timezone.now()
        self.antiquarian.lock(self.user)
        after = timezone.now()
        self.assertTrue(before < self.antiquarian.locked_at < after)

    def test_locked_by(self):
        self.antiquarian.lock(self.user)
        self.assertEqual(self.user, self.antiquarian.locked_by)
        self.antiquarian.unlock()
        self.assertIsNone(self.antiquarian.locked_by)

    def test_request_lock(self):
        other_user = UserFactory.create()
        self.antiquarian.lock(self.user)
        self.antiquarian.request_lock(other_user)
        self.assertEqual(other_user.objectlockrequest_set.count(), 1)
        # check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].subject, 'Request to edit record')
