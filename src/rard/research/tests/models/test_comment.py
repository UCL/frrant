import pytest
from unittest import skip
from django.db.utils import IntegrityError
from django.test import TestCase

from rard.research.models import Antiquarian, Comment, TextObjectField
from rard.users.models import User
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

@skip("Functionality to be deleted")
class TestComments(TestCase):

    def setUp(self):
        self.user = UserFactory.create()
        self.commentable = TextObjectField.objects.create(content='foo')

    def test_creation(self):
        data = {
            'user': self.user,
            'parent': self.commentable,
            'content': 'This is the comment'
        }
        comment = Comment.objects.create(**data)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

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

    def test_related_query_name_for_text_object_fields(self):
        data = {
            'user': self.user,
            'parent': self.commentable,
            'content': 'This is the comment'
        }
        comment = Comment.objects.create(**data)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
        self.assertEqual(self.commentable.comments.count(), 1)
        # text objects have a related query name to filter comments by
        # the fact they point to text fields
        self.assertEqual(
            Comment.objects.filter(
                text_fields__pk=self.commentable.pk
            ).count(), 1)

    def test_delete_parent_deletes_comment(self):
        data = {
            'user': self.user,
            'parent': self.commentable,
            'content': 'This is the comment'
        }
        comment = Comment.objects.create(**data)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
        self.commentable.delete()
        # NB this is only true when a GenericRelation exists on the
        # commented-on model
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_other_parent_type(self):
        # comment on a different object type
        antiquarian = Antiquarian.objects.create(name='name')
        data = {
            'user': self.user,
            'parent': antiquarian,
            'content': 'This is the comment'
        }
        comment = Comment.objects.create(**data)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

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
