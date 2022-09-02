import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingWork, Testimonium
from rard.research.views import (
    TestimoniumCreateView,
    TestimoniumDeleteView,
    TestimoniumDetailView,
    TestimoniumListView,
    TestimoniumUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTestimoniumSuccessUrls(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.citing_work = CitingWork.objects.create(title="title")

    def test_redirect_on_create(self):
        # data for both original text and testimonia
        data = {
            "apparatus_criticus": "app_criticus",
            "content": "content",
            "reference_order": 1,
            "citing_work": self.citing_work.pk,
            "citing_author": self.citing_work.author.pk,
            "create_object": True,
            "references-TOTAL_FORMS": 1,
            "references-INITIAL_FORMS": 0,
            "references-MIN_NUM_FORMS": 0,
            "references-MAX_NUM_FORMS": 1000,
            "references-0-id": "",
            "references-0-original_text": "",
            "references-0-editor": "geoff",
            "references-0-reference_position": "1.2.3",
            "create_object": True,
        }
        # assert no testimonia initially
        self.assertEqual(0, Testimonium.objects.count())

        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()

        response = TestimoniumCreateView.as_view()(
            request,
        )
        # we created an object
        self.assertEqual(1, Testimonium.objects.count())
        created = Testimonium.objects.first()
        # check we were redirected to the detail view of that object
        self.assertEqual(
            response.url, reverse("testimonium:detail", kwargs={"pk": created.pk})
        )

    def test_delete_success_url(self):
        view = TestimoniumDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Testimonium.objects.create(name="some name")

        self.assertEqual(view.get_success_url(), reverse("testimonium:list"))

    def test_update_success_url(self):
        view = TestimoniumUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Testimonium.objects.create(name="some name")

        self.assertEqual(
            view.get_success_url(),
            reverse("testimonium:detail", kwargs={"pk": view.object.pk}),
        )


class TestTestimoniumDeleteView(TestCase):
    def test_post_only(self):

        testimonium = Testimonium.objects.create(name="name")
        url = reverse("testimonium:delete", kwargs={"pk": testimonium.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TestimoniumDeleteView.as_view()(request, pk=testimonium.pk)
        self.assertEqual(response.status_code, 405)


class TestTestimoniumViewPermissions(TestCase):
    def test_permissions(self):

        self.assertIn(
            "research.add_testimonium", TestimoniumCreateView.permission_required
        )
        self.assertIn(
            "research.change_testimonium", TestimoniumUpdateView.permission_required
        )
        self.assertIn(
            "research.delete_testimonium", TestimoniumDeleteView.permission_required
        )
        self.assertIn(
            "research.view_testimonium", TestimoniumListView.permission_required
        )
        self.assertIn(
            "research.view_testimonium", TestimoniumDetailView.permission_required
        )
