import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, BibliographyItem
from rard.research.views import (AntiquarianBibliographyCreateView,
                                 BibliographyDeleteView,
                                 BibliographyUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestBibliographyViews(TestCase):

    def test_update_delete_create_top_level_object(self):

        # dispatch method creates an attribute used by the
        # locking mechanism so here we ensure it is created
        antiquarian = Antiquarian.objects.create(name='bob')
        bibitem = BibliographyItem.objects.create(
            author_name='author name',
            content='foo',
            parent=antiquarian
        )
        request = RequestFactory().post('/')
        request.user = UserFactory.create()

        for view_class in (BibliographyDeleteView, BibliographyUpdateView,):
            view = view_class()
            view.request = request
            view.kwargs = {'pk': bibitem.pk}
            view.dispatch(request)
            self.assertEqual(view.parent, antiquarian)


class TestBibliographyUpdateView(TestCase):

    def test_success_url(self):

        antiquarian = Antiquarian.objects.create(name='bob')
        bibitem = BibliographyItem.objects.create(
            author_name='author name',
            content='foo',
            parent=antiquarian
        )

        view = BibliographyUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = bibitem
        view.parent = antiquarian

        self.assertEqual(
            view.get_success_url(),
            antiquarian.get_absolute_url()
        )


class TestBibliographyDeleteView(TestCase):
    def test_post_only(self):

        antiquarian = Antiquarian.objects.create(name='bob')
        bibitem = BibliographyItem.objects.create(
            author_name='author name',
            content='foo',
            parent=antiquarian
        )
        url = reverse(
            'bibliography:delete',
            kwargs={'pk': bibitem.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = BibliographyDeleteView.as_view()(
            request, pk=bibitem.pk
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_success_url(self):

        antiquarian = Antiquarian.objects.create(name='bob')
        bibitem = BibliographyItem.objects.create(
            author_name='author name',
            content='foo',
            parent=antiquarian
        )

        view = BibliographyDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = bibitem
        view.parent = antiquarian

        self.assertEqual(
            view.get_success_url(),
            antiquarian.get_absolute_url()
        )


class TestBibliographyViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.delete_bibliographyitem',
            BibliographyDeleteView.permission_required
        )
        self.assertIn(
            'research.change_bibliographyitem',
            BibliographyUpdateView.permission_required
        )


class TestAntiquarianBibliographyCreateView(TestCase):

    def test_context_data(self):

        antiquarian = Antiquarian.objects.create()
        url = reverse(
            'antiquarian:create_bibliography',
            kwargs={'pk': antiquarian.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        antiquarian.lock(request.user)
        response = AntiquarianBibliographyCreateView.as_view()(
            request, pk=antiquarian.pk
        )

        self.assertEqual(
            response.context_data['antiquarian'], antiquarian
        )

    def test_success_url(self):

        view = AntiquarianBibliographyCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.antiquarian = Antiquarian.objects.create()

        self.assertEqual(
            view.get_success_url(),
            view.antiquarian.get_absolute_url()
        )

    def test_create(self):

        antiquarian = Antiquarian.objects.create()
        data = {'author_name': 'name', 'content': 'bib content'}
        url = reverse(
            'antiquarian:create_bibliography',
            kwargs={'pk': antiquarian.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()
        antiquarian.lock(request.user)

        self.assertEqual(
            antiquarian.bibliography_items.count(), 0
        )

        AntiquarianBibliographyCreateView.as_view()(
            request, pk=antiquarian.pk
        )
        self.assertEqual(
            antiquarian.bibliography_items.count(), 1
        )
        for key, val in data.items():
            self.assertEqual(
                getattr(antiquarian.bibliography_items.first(), key), val
            )

    def test_bad_data(self):
        antiquarian = Antiquarian.objects.create()
        data = {'bad': 'data'}
        url = reverse(
            'antiquarian:create_bibliography',
            kwargs={'pk': antiquarian.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()
        antiquarian.lock(request.user)

        AntiquarianBibliographyCreateView.as_view()(
            request, pk=antiquarian.pk
        )
        # no bibitem created
        self.assertEqual(
            antiquarian.bibliography_items.count(), 0
        )
