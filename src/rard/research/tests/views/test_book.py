import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Book, Work
from rard.research.views import BookCreateView, BookDeleteView, BookUpdateView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestBookUpdateView(TestCase):
    def test_context_data(self):

        work = Work.objects.create(name='name')
        book = Book.objects.create(work=work, number=1)
        url = reverse(
            'work:update_book',
            kwargs={'pk': book.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = BookUpdateView.as_view()(
            request, pk=book.pk
        )

        self.assertEqual(
            response.context_data['work'], work
        )

    def test_success_url(self):
        view = BookUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        work = Work.objects.create(name='name')
        view.object = Book.objects.create(number=1, work=work)

        self.assertEqual(
            view.get_success_url(),
            f"/work/{work.pk}/"
        )


class TestBookCreateView(TestCase):
    def test_context_data(self):

        work = Work.objects.create(name='name')
        url = reverse(
            'work:create_book',
            kwargs={'pk': work.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = BookCreateView.as_view()(
            request, pk=work.pk
        )

        self.assertEqual(
            response.context_data['work'], work
        )

    def test_success_url(self):
        view = BookCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.work = Work.objects.create()

        self.assertEqual(
            view.get_success_url(),
            f"/work/{view.work.pk}/"
        )

    def test_create(self):

        work = Work.objects.create()
        url = reverse(
            'work:create_book',
            kwargs={'pk': work.pk}
        )

        data = {'number': 1, 'subtitle': 'subtitle'}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        BookCreateView.as_view()(
            request, pk=work.pk
        )
        self.assertEqual(
            work.book_set.count(), 1
        )
        for key, val in data.items():
            self.assertEqual(getattr(work.book_set.first(), key), val)


class TestBookDeleteView(TestCase):
    def test_post_only(self):

        work = Work.objects.create(name='name')
        book = Book.objects.create(number=1, work=work)
        url = reverse(
            'work:delete_book',
            kwargs={'pk': book.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = BookDeleteView.as_view()(
            request, pk=book.pk
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_success_url(self):
        view = BookDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        work = Work.objects.create(name='name')
        view.object = Book.objects.create(number=1, work=work)

        self.assertEqual(
            view.get_success_url(),
            f"/work/{work.pk}/"
        )


class TestBookViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.add_book',
            BookCreateView.permission_required
        )
        self.assertIn(
            'research.delete_book',
            BookDeleteView.permission_required
        )
        self.assertIn(
            'research.change_book',
            BookUpdateView.permission_required
        )
