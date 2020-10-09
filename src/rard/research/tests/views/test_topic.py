import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Topic
from rard.research.views import (TopicCreateView, TopicDeleteView,
                                 TopicDetailView,
                                 TopicListView,
                                 TopicUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTopicSuccessUrls(TestCase):

    def test_update_success_url(self):
        view = TopicUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Topic.objects.create(name='some name')

        self.assertEqual(
            view.get_success_url(),
            reverse('topic:detail', kwargs={'slug': view.object.slug})
        )

    def test_create_success_url(self):
        view = TopicCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Topic.objects.create(name='some name')

        self.assertEqual(
            view.get_success_url(),
            reverse('topic:list')
        )

    def test_delete_success_url(self):
        view = TopicDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Topic.objects.create(name='some name')

        self.assertEqual(
            view.get_success_url(),
            reverse('topic:list')
        )


class TestTopicDeleteView(TestCase):
    def test_post_only(self):

        topic = Topic.objects.create(name='name')
        url = reverse(
            'topic:delete',
            kwargs={'slug': topic.slug}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TopicDeleteView.as_view()(
            request, pk=topic.pk
        )
        self.assertEqual(response.status_code, 405)


class TestTopicViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.add_topic', TopicCreateView.permission_required
        )
        self.assertIn(
            'research.delete_topic', TopicDeleteView.permission_required
        )
        self.assertIn(
            'research.change_topic', TopicUpdateView.permission_required
        )
        self.assertIn(
            'research.view_topic', TopicListView.permission_required
        )
        self.assertIn(
            'research.view_topic', TopicDetailView.permission_required
        )
