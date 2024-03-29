import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingAuthor, CitingWork, OriginalText
from rard.research.models.fragment import AnonymousFragment, Fragment
from rard.research.models.testimonium import Testimonium
from rard.research.views import (
    CitingAuthorDetailView,
    CitingAuthorListView,
    CitingWorkDeleteView,
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


class TestCitingWorkViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn(
            "research.change_citingwork", CitingWorkUpdateView.permission_required
        )
        self.assertIn(
            "research.delete_citingwork", CitingWorkDeleteView.permission_required
        )
        self.assertIn(
            "research.view_citingwork", CitingWorkDetailView.permission_required
        )
        self.assertIn(
            "research.view_citingauthor", CitingAuthorListView.permission_required
        )
        self.assertIn(
            "research.view_citingwork", CitingAuthorListView.permission_required
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
