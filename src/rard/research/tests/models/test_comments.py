from uuid import UUID

import pytest
from django.db.utils import IntegrityError
from django.test import TestCase

from rard.research.models import Comment, CommentableText
from rard.users.models import User
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCommentableText(TestCase):

    def test_required_fields(self):
        self.assertTrue(CommentableText._meta.get_field('content').blank)

    def test_creation(self):
        text = CommentableText.objects.create()
        self.assertIsInstance(text.pk, UUID)

    def test_default_value(self):
        text = CommentableText.objects.create()
        self.assertEqual(text.content, '')

    def test_stored_value(self):
        content = 'some content'
        text = CommentableText.objects.create(content=content)
        self.assertEqual(text.content, content)


class TestComments(TestCase):

    def setUp(self):
        self.user = UserFactory.create()
        self.commentable = CommentableText.objects.create(content='foo')

    def test_creation(self):
        data = {
            'user': self.user,
            'parent': self.commentable,
            'content': 'This is the comment'
        }
        comment = Comment.objects.create(**data)
        self.assertIsInstance(comment.pk, UUID)

    def test_required_fields(self):
        self.assertFalse(Comment._meta.get_field('content').blank)

    def test_user_required(self):
        data = {
            'parent': self.commentable,
            'content': 'This is the comment'
        }
        # cannot create a comment with no user
        with self.assertRaises(IntegrityError):
            Comment.objects.create(**data)

    def test_parent_required(self):
        data = {
            'user': self.user,
            'content': 'This is the comment'
        }
        # cannot create a comment with no parent
        with self.assertRaises(IntegrityError):
            Comment.objects.create(**data)

    def test_persist_comment_on_user_deletion(self):
        # deleting comment author does not delete the comment instead
        # reset the comment auhor to sentinel 'deleted user'
        data = {
            'user': self.user,
            'parent': self.commentable,
            'content': 'This is the comment'
        }
        comment = Comment.objects.create(**data)
        comment_pk = comment.pk
        user_pk = self.user.pk
        self.user.delete()

        # the comment should still be there
        refetch = Comment.objects.get(pk=comment_pk)

        # and the user should be 'deleted user'
        self.assertNotEqual(refetch.user.pk, user_pk)
        self.assertIsNotNone(refetch.user.pk)
        self.assertEqual(refetch.user.username, User.SENTINEL_USERNAME)
