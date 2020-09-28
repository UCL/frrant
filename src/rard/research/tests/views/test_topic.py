import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Topic
from rard.research.views import (TopicCreateView, TopicDeleteView,
                                 TopicUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTopicSuccessUrls(TestCase):

    def test_update_success_url(self):
        views = [
            TopicCreateView,
            TopicUpdateView,
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = UserFactory.create()

            view.request = request
            view.object = Topic.objects.create(name=view_class.__name__)

            self.assertEqual(
                view.get_success_url(),
                reverse('topic:detail', kwargs={'slug': view.object.slug})
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
