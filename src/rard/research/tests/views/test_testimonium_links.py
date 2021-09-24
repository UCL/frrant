import pytest
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, Testimonium, Work
from rard.research.models.base import TestimoniumLink
from rard.research.views import RemoveTestimoniumLinkView, TestimoniumAddWorkLinkView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTestimoniumAddWorkLinkView(TestCase):
    def test_success_url(self):
        view = TestimoniumAddWorkLinkView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.testimonium = Testimonium.objects.create(name="name")

        view.testimonium.lock(request.user)

        self.assertEqual(
            view.get_success_url(),
            reverse("testimonium:detail", kwargs={"pk": view.testimonium.pk}),
        )

    def test_create_link_post(self):

        testimonium = Testimonium.objects.create(name="name")
        antiquarian = Antiquarian.objects.create(name="name", re_code=1)
        work = Work.objects.create(name="name")
        antiquarian.works.add(work)
        url = reverse("testimonium:add_work_link", kwargs={"pk": testimonium.pk})
        data = {"antiquarian": antiquarian.pk, "work": work.pk}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        testimonium.lock(request.user)

        self.assertEqual(TestimoniumLink.objects.count(), 0)
        TestimoniumAddWorkLinkView.as_view()(request, pk=testimonium.pk)
        self.assertEqual(TestimoniumLink.objects.count(), 1)
        link = TestimoniumLink.objects.first()
        self.assertEqual(link.testimonium, testimonium)
        self.assertEqual(link.work, work)

    def test_context_data(self):
        testimonium = Testimonium.objects.create(name="name")
        work = Work.objects.create(name="name")
        url = reverse("testimonium:add_work_link", kwargs={"pk": testimonium.pk})
        data = {"work": work.pk}
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()

        testimonium.lock(request.user)

        response = TestimoniumAddWorkLinkView.as_view()(request, pk=testimonium.pk)
        self.assertEqual(response.context_data["work"], work)
        self.assertEqual(response.context_data["testimonium"], testimonium)

    def test_bad_data(self):

        testimonium = Testimonium.objects.create(name="name")
        work = Work.objects.create(name="name")
        url = reverse("testimonium:add_work_link", kwargs={"pk": testimonium.pk})
        data = {"work": work.pk + 101}  # bad value
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()

        testimonium.lock(request.user)

        with self.assertRaises(Http404):
            TestimoniumAddWorkLinkView.as_view()(request, pk=testimonium.pk)

    def test_permission_required(self):
        self.assertIn(
            "research.change_testimonium",
            TestimoniumAddWorkLinkView.permission_required,
        )


class TestTestimoniumRemoveWorkLinkView(TestCase):
    def test_success_url(self):
        testimonium = Testimonium.objects.create(name="name")
        work = Work.objects.create(name="name")
        TestimoniumLink.objects.create(work=work, testimonium=testimonium)

        view = RemoveTestimoniumLinkView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.testimonium = testimonium

        self.assertEqual(
            view.get_success_url(),
            reverse("testimonium:detail", kwargs={"pk": testimonium.pk}),
        )

    def test_delete_link_post(self):

        testimonium = Testimonium.objects.create(name="name")
        work = Work.objects.create(name="name")
        link = TestimoniumLink.objects.create(work=work, testimonium=testimonium)

        request = RequestFactory().post("/")
        request.user = UserFactory.create()

        testimonium.lock(request.user)

        self.assertEqual(TestimoniumLink.objects.count(), 1)
        RemoveTestimoniumLinkView.as_view()(request, pk=link.pk)
        self.assertEqual(TestimoniumLink.objects.count(), 0)

    def test_permission_required(self):
        self.assertIn(
            "research.change_testimonium", RemoveTestimoniumLinkView.permission_required
        )
