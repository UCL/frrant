import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    CitingAuthor,
    CitingWork,
    Fragment,
    Topic,
)
from rard.research.models.original_text import OriginalText
from rard.research.views import (
    TopicCreateView,
    TopicDeleteView,
    TopicDetailView,
    TopicListView,
    TopicUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTopicSuccessUrls(TestCase):
    def test_update_success_url(self):
        view = TopicUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Topic.objects.create(name="some name")

        self.assertEqual(
            view.get_success_url(),
            reverse("topic:detail", kwargs={"slug": view.object.slug}),
        )

    def test_create_success_url(self):
        view = TopicCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Topic.objects.create(name="some name")

        self.assertEqual(view.get_success_url(), reverse("topic:list"))

    def test_delete_success_url(self):
        view = TopicDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Topic.objects.create(name="some name")

        self.assertEqual(view.get_success_url(), reverse("topic:list"))


class TestTopicListView(TestCase):
    def setUp(self):
        self.names = ["art", "science", "politics"]
        for name in self.names:
            Topic.objects.create(name=name)

    def test_order(self):
        self.assertEqual([x.name for x in Topic.objects.all()], self.names)

    def test_post_up(self):
        # move the last topic up

        data = {
            "topic_id": Topic.objects.get(name="politics").pk,
            "up": "",
        }

        url = reverse("topic:list")

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        TopicListView.as_view()(
            request,
        )

        self.assertEqual(
            [x.name for x in Topic.objects.all()],
            [
                "art",
                "politics",
                "science",
            ],
        )

    def test_post_down(self):
        # move the first one down

        data = {
            "topic_id": Topic.objects.get(name="art").pk,
            "down": "",
        }

        url = reverse("topic:list")

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        TopicListView.as_view()(
            request,
        )

        self.assertEqual(
            [x.name for x in Topic.objects.all()],
            [
                "science",
                "art",
                "politics",
            ],
        )

    def test_redirect_on_bad_data(self):
        data = {
            "topic_id": 999,
            "down": "",
        }

        url = reverse("topic:list")

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        response = TopicListView.as_view()(
            request,
        )

        # check the data is unchanged
        self.assertEqual([x.name for x in Topic.objects.all()], self.names)

        # and that we were redirected to the same url
        self.assertEqual(response.url, url)


class TestTopicUpdateView(TestCase):
    def test_update_view(self):
        topic = Topic.objects.create(name="some name")
        NEW_NAME = "new name"
        request = RequestFactory().post("/", data={"name": NEW_NAME})
        request.user = UserFactory.create()

        topic.lock(request.user)

        TopicUpdateView.as_view()(request, pk=topic.pk)

        # check data was updated
        refresh = Topic.objects.get(pk=topic.pk)
        self.assertEqual(refresh.name, NEW_NAME)


class TestTopicDeleteView(TestCase):
    def test_post_only(self):
        topic = Topic.objects.create(name="name")
        url = reverse("topic:delete", kwargs={"slug": topic.slug})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TopicDeleteView.as_view()(request, pk=topic.pk)
        self.assertEqual(response.status_code, 405)


class TestTopicViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn("research.add_topic", TopicCreateView.permission_required)
        self.assertIn("research.delete_topic", TopicDeleteView.permission_required)
        self.assertIn("research.change_topic", TopicUpdateView.permission_required)
        self.assertIn("research.view_topic", TopicListView.permission_required)
        self.assertIn("research.view_topic", TopicDetailView.permission_required)


class TestTopicDetailView(TestCase):
    def setUp(self):
        """Create two fragments and two anonymous fragments
        linked to a topic with different authors"""
        # Create a topic
        self.topic_name = "test_topic"
        self.topic = Topic.objects.create(name=self.topic_name)

        # We want two authors so we can test alternate ordering
        self.citing_author_a = CitingAuthor.objects.create(name="Alice")
        self.citing_author_b = CitingAuthor.objects.create(name="Bob")
        self.citing_work_1 = CitingWork.objects.create(
            title="title_1", author=self.citing_author_b
        )
        self.citing_work_2 = CitingWork.objects.create(
            title="title_2", author=self.citing_author_a
        )
        # create fragments and anonymous fragments which will be
        # owners of original texts
        self.fragment_1 = Fragment.objects.create(name="f1a")
        self.anonymous_1 = AnonymousFragment.objects.create(name="f1b")
        self.fragment_2 = Fragment.objects.create(name="f2a")
        self.anonymous_2 = AnonymousFragment.objects.create(name="f2b")

        self.originaltext_1a = OriginalText.objects.create(
            citing_work=self.citing_work_1, content="blah", owner=self.fragment_1
        )
        self.originaltext_1b = OriginalText.objects.create(
            citing_work=self.citing_work_1, content="blah", owner=self.anonymous_1
        )
        self.originaltext_2a = OriginalText.objects.create(
            citing_work=self.citing_work_2, content="blah", owner=self.fragment_2
        )
        self.originaltext_2b = OriginalText.objects.create(
            citing_work=self.citing_work_2, content="blah", owner=self.anonymous_2
        )

        self.user = UserFactory.create()

        self.topic_items = [
            self.fragment_1,
            self.anonymous_1,
            self.fragment_2,
            self.anonymous_2,
        ]

        for i in self.topic_items:
            i.topics.add(self.topic)

    def test_antiquarian_order(self):
        request = RequestFactory().get("/")
        request.user = self.user
        response = TopicDetailView.as_view()(request, slug=self.topic_name)
        antiquarian_order = [self.topic_items[i] for i in [0, 2, 1, 3]]
        combined_context_list = (
            response.context_data["fragments"]
            + response.context_data["anonymous_fragments"]
        )
        self.assertEqual(antiquarian_order, combined_context_list)

    def test_citing_author_order(self):
        request = RequestFactory().get("/?order=citing_author")
        request.user = self.user
        response = TopicDetailView.as_view()(request, slug=self.topic_name)
        author_order = [self.topic_items[i] for i in [2, 0, 3, 1]]
        combined_context_list = (
            response.context_data["fragments"]
            + response.context_data["anonymous_fragments"]
        )
        self.assertEqual(author_order, combined_context_list)
