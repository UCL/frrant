from unittest import skip

import pytest
from django.db.utils import IntegrityError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Comment, Fragment, TextObjectField
from rard.research.views import (CommentDeleteView,
                                 TextObjectFieldCommentListView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@skip("Functionality to be deleted")
class TestCommentListView(TestCase):

    def test_create_get_parent(self):
        fragment = Fragment.objects.create(name='name')
        view = TextObjectFieldCommentListView()

        request = RequestFactory().get("/")
        request.user = UserFactory.create()
        request.path = '/'
        view.request = request
        view.kwargs = {'pk': fragment.commentary.pk}

        self.assertEqual(
            view.get_parent_object(),
            fragment.commentary
        )

    def test_queryset(self):

        # create comments on two fragments and check our list view
        # only shows the relevant set
        fragment1 = Fragment.objects.create(name='fragment1')
        fragment2 = Fragment.objects.create(name='fragment2')

        user = UserFactory.create()
        # create comments on fragment1
        for _ in range(0, 100):
            Comment.objects.create(
                content='hello',
                user=user,
                parent=fragment1.commentary
            )
        # create comments on fragment2
        for _ in range(0, 99):
            Comment.objects.create(
                content='hi',
                user=user,
                parent=fragment2.commentary
            )

        view = TextObjectFieldCommentListView()

        request = RequestFactory().get("/")
        request.user = UserFactory.create()
        view.request = request
        view.kwargs = {'pk': fragment1.commentary.pk}

        # we should only list the comments of fragment1
        self.assertEqual(
            view.get_queryset().count(), 100
        )
        for comment in view.get_queryset().all():
            self.assertEqual(comment.parent.pk, fragment1.commentary.pk)

    def test_context_data(self):

        fragment = Fragment.objects.create(name='fragment1')
        url = reverse(
            'list_comments_on_text',
            kwargs={'pk': fragment.commentary.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TextObjectFieldCommentListView.as_view()(
            request, pk=fragment.commentary.pk
        )

        self.assertEqual(
            response.context_data['parent_object'], fragment.commentary
        )

    def test_creation_post(self):
        fragment = Fragment.objects.create(name='name')

        url = reverse(
            'list_comments_on_text',
            kwargs={'pk': fragment.commentary.pk}
        )

        data = {
            'content': 'content',
            'parent': fragment.commentary
        }
        self.assertEqual(0, Comment.objects.count())

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        TextObjectFieldCommentListView.as_view()(
            request, pk=fragment.commentary.pk
        )
        # check we created a comment
        self.assertEqual(1, Comment.objects.count())
        created = Comment.objects.first()
        # check its parent
        self.assertEqual(created.parent, fragment.commentary)
        # check that user is taken from the request
        self.assertEqual(created.user, request.user)

    def test_blank_comment_invalid(self):
        fragment = Fragment.objects.create(name='name')

        url = reverse(
            'list_comments_on_text',
            kwargs={'pk': fragment.commentary.pk}
        )

        data = {
            'content': '',  # blank content should fail
        }
        self.assertEqual(0, Comment.objects.count())

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        TextObjectFieldCommentListView.as_view()(
            request, pk=fragment.commentary.pk
        )
        # no comment created
        self.assertEqual(0, Comment.objects.count())


@skip("Functionality to be deleted")
class TestTextCommentView(TestCase):
    def test_class_setup(self):
        self.assertEqual(
            TextObjectFieldCommentListView.parent_object_class,
            TextObjectField
        )


@skip("Functionality to be deleted")
class TestCommentView(TestCase):

    def test_creation(self):
        fragment = Fragment.objects.create(name='name')
        user = UserFactory.create()
        comment = Comment.objects.create(
            content='content',
            user=user,
            parent=fragment.commentary,
        )
        self.assertEqual(fragment.commentary, comment.parent)

    def test_user_required(self):
        fragment = Fragment.objects.create(name='name')
        with self.assertRaises(IntegrityError):
            Comment.objects.create(
                content='content',
                parent=fragment.commentary
            )


@skip("Functionality to be deleted")
class TestCommentDeleteView(TestCase):

    def setUp(self):
        self.fragment = Fragment.objects.create(name='name')
        self.user = UserFactory.create()
        self.comment = Comment.objects.create(
            content='content',
            user=self.user,
            parent=self.fragment.commentary,
        )

    def test_post_only(self):
        url = reverse(
            'delete_comment',
            kwargs={'pk': self.comment.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = CommentDeleteView.as_view()(
            request, pk=self.comment.pk
        )
        self.assertEqual(response.status_code, 405)

    def test_queryset(self):
        view = CommentDeleteView()
        request = RequestFactory().get("/")
        request.user = self.user

        view.request = request
        view.object = self.comment

        # create a load of comments by another user
        # on the same fragment
        other_user = UserFactory.create()
        for _ in range(0, 100):
            Comment.objects.create(
                content='content',
                user=other_user,
                parent=self.fragment.commentary,
            )
        other_comments = Comment.objects.filter(user=other_user)
        self.assertEqual(100, other_comments.count())

        # the delete view should only be able to delete our own
        my_comments = Comment.objects.filter(user=self.user)
        self.assertEqual(
            sorted([c.pk for c in my_comments.all()]),
            sorted([c.pk for c in view.get_queryset().all()]),
        )

    def test_success_url(self):
        view = CommentDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        # set up the referer
        request.META = {}
        dummy_url = '/redirect-to-here/'
        request.META['HTTP_REFERER'] = dummy_url

        view.request = request
        view.object = self.comment

        self.assertEqual(
            view.get_success_url(),
            dummy_url
        )


@skip("Functionality to be deleted")
class TestCommentViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.delete_comment',
            CommentDeleteView.permission_required
        )
        self.assertIn(
            'research.view_comment',
            TextObjectFieldCommentListView.permission_required
        )
