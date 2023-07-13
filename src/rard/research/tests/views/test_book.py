import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Book, Work
from rard.research.views import (
    BookCreateView,
    BookDeleteView,
    BookUpdateIntroductionView,
    BookUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestBookUpdateView(TestCase):
    def test_context_data(self):
        work = Work.objects.create(name="name")
        book = Book.objects.create(work=work, number=1)
        url = reverse("work:update_book", kwargs={"pk": book.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()

        work.lock(request.user)

        response = BookUpdateView.as_view()(request, pk=book.pk)

        self.assertEqual(response.context_data["work"], work)

    def test_success_url(self):
        view = BookUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        work = Work.objects.create(name="name")

        work.lock(request.user)

        view.object = Book.objects.create(number=1, work=work)

        self.assertEqual(view.get_success_url(), f"/work/{work.pk}/")


class TestBookUpdateIntroductionView(TestCase):
    def setUp(self):
        self.work = Work.objects.create(name="name")
        self.book = Book.objects.create(work=self.work, number=1)
        self.url = reverse("work:update_book_introduction", kwargs={"pk": self.book.pk})
        self.request = RequestFactory().get(self.url)
        self.request.user = UserFactory.create()

        self.work.lock(self.request.user)

        self.response = BookUpdateIntroductionView.as_view()(
            self.request, pk=self.book.pk
        )

    def test_context_data(self):
        self.assertEqual(
            self.response.context_data["text_object"], self.book.introduction
        )
        self.assertEqual(self.response.context_data["object_class"], "book")

    def test_success_url(self):
        # this is more complicated than with other views
        # due to the conditional rendering on another view
        # // I think
        success_url = self.response.context_data["view"].get_success_url()
        self.assertEqual(success_url, f"/work/{self.work.pk}/")

    def test_update_intro(self):
        """This checks that an introduction object is created
        when the book object is created but is empty
        and will update on POST"""
        intro = self.response.context_data["object"].introduction

        self.assertTrue(bool(intro.pk))
        self.assertFalse(bool(intro.content))

        book_pk = self.response.context_data["object"].pk

        intro_text = "testing update of introduction"

        data = {
            "introduction_text": intro_text,
        }
        post_request = RequestFactory().post(self.url, data=data)
        post_request.user = self.request.user
        BookUpdateIntroductionView.as_view()(post_request, pk=book_pk)

        view = BookUpdateIntroductionView.as_view()(self.request, pk=self.book.pk)

        intro = view.context_data["object"].introduction
        self.assertTrue(bool(intro.content))
        self.assertEqual(intro.content, intro_text)


class TestBookCreateView(TestCase):
    def test_context_data(self):
        work = Work.objects.create(name="name")
        url = reverse("work:create_book", kwargs={"pk": work.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()

        work.lock(request.user)

        response = BookCreateView.as_view()(request, pk=work.pk)

        self.assertEqual(response.context_data["work"], work)

    def test_success_url(self):
        view = BookCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.work = Work.objects.create()

        view.work.lock(request.user)

        self.assertEqual(view.get_success_url(), f"/work/{view.work.pk}/")

    def test_create(self):
        work = Work.objects.create(name="name")
        url = reverse("work:create_book", kwargs={"pk": work.pk})

        data = {"number": 1, "subtitle": "subtitle"}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        work.lock(request.user)
        BookCreateView.as_view()(request, pk=work.pk)
        self.assertEqual(work.book_set.exclude(unknown=True).count(), 1)
        for key, val in data.items():
            self.assertEqual(
                getattr(work.book_set.exclude(unknown=True).first(), key), val
            )
        self.assertIn(work.unknown_book, work.book_set.all())
        self.assertTrue(work.book_set.first().introduction)


class TestBookDeleteView(TestCase):
    def test_post_only(self):
        work = Work.objects.create(name="name")
        book = Book.objects.create(number=1, work=work)
        url = reverse("work:delete_book", kwargs={"pk": book.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = BookDeleteView.as_view()(request, pk=book.pk)
        self.assertEqual(response.status_code, 405)

    def test_delete_success_url(self):
        view = BookDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        work = Work.objects.create(name="name")
        view.object = Book.objects.create(number=1, work=work)

        self.assertEqual(view.get_success_url(), f"/work/{work.pk}/")


class TestBookViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn("research.add_book", BookCreateView.permission_required)
        self.assertIn("research.delete_book", BookDeleteView.permission_required)
        self.assertIn("research.change_book", BookUpdateView.permission_required)
