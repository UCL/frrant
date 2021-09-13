import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    Topic,
    CitingWork,
    CitingAuthor,
    Fragment,
    AnonymousFragment,
)
from rard.research.views import (
    TopicCreateView,
    TopicDeleteView,
    TopicDetailView,
    TopicListView,
    TopicUpdateView,
    FragmentCreateView,
    AnonymousFragmentCreateView,
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

        # Create two fragments and two anonymous fragments
        # linked to this topic with different authors
        self.user = UserFactory.create()
        fragment_1 = {
            "name": "fragment 1",
            "apparatus_criticus": "app_criticus",
            "content": "content",
            "reference": "Page 1",
            "reference_order": 1,
            "topics": [self.topic.pk],
            "citing_work": self.citing_work_1.pk,
            "citing_author": self.citing_work_1.author.pk,
            "create_object": True,
        }
        fragment_2 = fragment_1.copy()
        fragment_2["name"] = "fragment 2"
        fragment_2["citing_work"] = self.citing_work_2.pk
        fragment_2["citing_author"] = self.citing_work_2.author.pk
        self.topic_items = []
        for fragment in [fragment_1, fragment_2]:
            request = RequestFactory().post("/", data=fragment)
            request.user = self.user
            response = FragmentCreateView.as_view()(request)
            self.topic_items.append(
                Fragment.objects.filter(pk=response.url.split("/")[2]).first()
            )
            response = AnonymousFragmentCreateView.as_view()(request)
            self.topic_items.append(
                AnonymousFragment.objects.filter(pk=response.url.split("/")[2]).first()
            )

    def test_antiquarian_order(self):
        request = RequestFactory().get("/")
        request.user = self.user
        response = TopicDetailView.as_view()(request, slug=self.topic_name)
        antiquarian_order = [self.topic_items[i] for i in [0, 2, 1, 3]]
        self.assertEqual(antiquarian_order, response.context_data["fragments"])

    def test_citing_author_order(self):
        request = RequestFactory().get("/?order=citing_author")
        request.user = self.user
        response = TopicDetailView.as_view()(request, slug=self.topic_name)
        author_order = [self.topic_items[i] for i in [2, 0, 3, 1]]
        self.assertEqual(author_order, response.context_data["fragments"])
