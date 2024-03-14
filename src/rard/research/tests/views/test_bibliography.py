import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, BibliographyItem  # , bibliography
from rard.research.views import (
    BibliographyCreateView,
    BibliographyDeleteView,
    BibliographyUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestBibliographyUpdateView(TestCase):
    def test_success_url(self):
        bibitem = BibliographyItem.objects.create(
            authors="author name",
            author_surnames="author",
            title="foo",
        )

        view = BibliographyUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = bibitem

        self.assertEqual(view.get_success_url(), bibitem.get_absolute_url())


class TestBibliographyDeleteView(TestCase):
    def test_post_only(self):
        bibitem = BibliographyItem.objects.create(
            authors="author name",
            author_surnames="author",
            title="foo",
        )
        url = reverse("bibliography:delete", kwargs={"pk": bibitem.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = BibliographyDeleteView.as_view()(request, pk=bibitem.pk)
        self.assertEqual(response.status_code, 405)

    def test_delete_success_url(self):
        bibitem = BibliographyItem.objects.create(
            authors="author name",
            author_surnames="author",
            title="foo",
        )

        view = BibliographyDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = bibitem

        self.assertEqual(view.get_success_url(), reverse("bibliography:overview"))


class TestBibliographyViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn(
            "research.delete_bibliographyitem",
            BibliographyDeleteView.permission_required,
        )
        self.assertIn(
            "research.change_bibliographyitem",
            BibliographyUpdateView.permission_required,
        )


class TestBibliographyCreateView(TestCase):
    def test_create(self):
        a1 = Antiquarian.objects.create(name="foo", re_code=3)
        a2 = Antiquarian.objects.create(name="zoo", re_code=4)
        data = {
            "authors": "name",
            "author_surnames": "name",
            "title": "bib title",
            "antiquarians": [a1.pk, a2.pk],
        }
        url = reverse("bibliography:create")

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        self.assertEqual(BibliographyItem.objects.count(), 0)
        self.bibliography = BibliographyCreateView.as_view()(request)
        # should now be 1
        self.assertEqual(BibliographyItem.objects.count(), 1)
        # should get a list of 2 antiquarians attachec to the bibliography
        self.assertEqual(BibliographyItem.objects.first().antiquarians.count(), 2)

    def test_success_url(self):
        view = BibliographyCreateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = BibliographyItem.objects.create()

        self.assertEqual(view.get_success_url(), f"/bibliography/{view.object.pk}/")

    def test_bad_data(self):
        data = {"bad": "data"}
        url = reverse("bibliography:create")

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        self.assertEqual(BibliographyItem.objects.count(), 0)
        BibliographyCreateView.as_view()(request)
        # no bibitem created, still 0
        self.assertEqual(BibliographyItem.objects.count(), 0)

    def test_surname_ordering(self):
        data = [
            {
                "pk": 1,
                "title": "foo",
                "authors": "aaa This should be Last",
                "author_surnames": "zzz",
            },
            {
                "pk": 2,
                "title": "bar",
                "authors": "zzz This should be First",
                "author_surnames": "aaa",
            },
            {
                "pk": 3,
                "title": "bar",
                "authors": "zzz This should be in the middle",
                "author_surnames": "ggg",
            },
        ]
        for d in data:
            BibliographyItem.objects.create(**d)

        self.assertEqual([2, 3, 1], [x.pk for x in BibliographyItem.objects.all()])

    def test_year_ordering(self):
        year_data = [
            {
                "pk": 1,
                "year": "1440a",
            },
            {
                "pk": 2,
                "year": "1430",
            },
            {
                "pk": 3,
                "year": "1440b",
            },
            {
                "pk": 4,
                "year": "1155",
            },
            {
                "pk": 5,
                "year": "1440e",
            },
            {
                "pk": 6,
                "year": "1440c",
            },
            {
                "pk": 7,
                "year": "1440d",
            },
        ]
        # keep other fields the same so we can be sure we order by year
        # if everything else the same
        common_data = {
            "title": "hello",
            "authors": "author name",
            "author_surnames": "author",
        }
        for d in year_data:
            BibliographyItem.objects.create(**d, **common_data)

        self.assertEqual(
            [4, 2, 1, 3, 6, 7, 5], [x.pk for x in BibliographyItem.objects.all()]
        )
