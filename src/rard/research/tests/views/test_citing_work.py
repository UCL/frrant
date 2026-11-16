import pytest
from django.contrib.auth.models import AnonymousUser
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingAuthor, CitingWork, OriginalText
from rard.research.models.fragment import AnonymousFragment, Fragment
from rard.research.models.testimonium import Testimonium
from rard.research.views import (
    CitingAuthorDetailView,
    CitingWorkDetailView,
    CitingWorkUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCitingWorkUpdateView(TestCase):
    def test_success_url(self):
        view = CitingWorkUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = CitingWork.objects.create(title="title")

        self.assertEqual(
            view.get_success_url(),
            reverse("citingauthor:work_detail", kwargs={"pk": view.object.pk}),
        )


class TestCitingAuthorDetailView(TestCase):
    def setUp(self):
        # Create a citing author
        self.citing_author = CitingAuthor.objects.create(name="Alice")
        # Create two citing works
        self.work1 = CitingWork.objects.create(
            author=self.citing_author, title="Work 1"
        )
        self.work2 = CitingWork.objects.create(
            author=self.citing_author, title="Work 2"
        )
        # Create two fragments, two testimonia, and two anonymous fragments
        # One for each citing work, with varying reference orders
        self.user = UserFactory.create()
        text_names = ["f1", "f2", "t1", "t2", "a1", "a2"]
        reference_orders = ["1.1.1", "1.1.2", "1.1.12", "1.2.1", "1.12.1", "12.1.1"]
        model_types = [Fragment] * 2 + [Testimonium] * 2 + [AnonymousFragment] * 2
        citing_works = [self.work1, self.work2] * 3
        self.texts = []
        for i in range(6):
            fragment = model_types[i].objects.create(name=text_names[i])
            OriginalText.objects.create(
                content="content",
                reference_order=reference_orders[i],
                citing_work=citing_works[i],
                owner=fragment,
            )

            self.texts.append(fragment)
        self.ordered_texts = [self.texts[i] for i in [0, 2, 4, 1, 3, 5]]

    def test_order_by_work_then_reference(self):
        request = RequestFactory().get("/")
        request.user = self.user
        response = CitingAuthorDetailView.as_view()(request, pk=self.citing_author.id)
        response_order = [
            item[1] for item in response.context_data["ordered_materials"]
        ]
        self.assertEqual(self.ordered_texts, response_order)

    def request_detail(self, pk):
        request = RequestFactory().get(
            reverse(
                "citingauthor:detail",
                kwargs={"pk": pk},
            )
        )
        request.user = AnonymousUser()
        return CitingAuthorDetailView.as_view()(request, pk=pk)

    def test_unauthorised_can_only_view_published(self):
        published = CitingAuthor.objects.create(name="John Published")
        published.publishable = True
        published.save()
        unpublished = CitingAuthor.objects.create(name="Dan Unready")
        response_pub = self.request_detail(published.pk)
        self.assertEqual(response_pub.status_code, 200)
        self.assertRaises(
            Http404,
            self.request_detail,
            unpublished.pk,
        )

    def request_work_detail(self, pk):
        request = RequestFactory().get(
            reverse(
                "citingauthor:work_detail",
                kwargs={"pk": pk},
            )
        )
        request.user = AnonymousUser()
        return CitingWorkDetailView.as_view()(request, pk=pk)

    def test_unauthorised_can_only_view_published_work(self):
        published = CitingWork.objects.create(title="published work")
        published.publishable = True
        published.save()
        unpublished = CitingWork.objects.create(title="not ready yet")
        response_pub = self.request_work_detail(published.pk)
        self.assertEqual(response_pub.status_code, 200)
        self.assertRaises(
            Http404,
            self.request_work_detail,
            unpublished.pk,
        )
