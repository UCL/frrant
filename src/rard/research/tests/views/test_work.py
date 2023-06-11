import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, Book, Fragment, Testimonium, Work
from rard.research.models.base import FragmentLink, TestimoniumLink
from rard.research.views import (
    WorkCreateView,
    WorkDeleteView,
    WorkDetailView,
    WorkListView,
    WorkUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestWorkSuccessUrls(TestCase):
    def test_update_success_url(self):
        views = [
            WorkUpdateView,
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = UserFactory.create()

            view.request = request
            view.object = Work()

            self.assertEqual(view.get_success_url(), f"/work/{view.object.pk}/")

    def test_delete_success_url(self):
        view = WorkDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Work()

        self.assertEqual(view.get_success_url(), reverse("work:list"))


class TestWorkDeleteView(TestCase):
    def test_post_only(self):
        work = Work.objects.create(name="name")
        url = reverse("work:delete", kwargs={"pk": work.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = WorkDeleteView.as_view()(request, pk=work.pk)
        self.assertEqual(response.status_code, 405)


class TestWorkViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn("research.add_work", WorkCreateView.permission_required)
        self.assertIn("research.delete_work", WorkDeleteView.permission_required)
        self.assertIn("research.change_work", WorkUpdateView.permission_required)
        self.assertIn("research.view_work", WorkListView.permission_required)
        self.assertIn("research.view_work", WorkDetailView.permission_required)


class TestWorkCreateView(TestCase):
    def test_create(self):
        url = reverse("work:create")
        a = Antiquarian.objects.create(name="foo", re_code=1)
        data = {"antiquarians": [a.pk], "name": "work name"}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        WorkCreateView.as_view()(request)
        a = Antiquarian.objects.get(pk=a.pk)
        self.assertEqual(a.works.exclude(unknown=True).count(), 1)
        self.assertIn(a.unknown_work, a.works.all())

    def test_create_with_books(self):
        url = reverse("work:create")
        a = Antiquarian.objects.create(name="bar", re_code=2)
        data = {
            "antiquarians": [a.pk],
            "name": "another name",
            "books_0_num": 2,
            "books_0_title": "deux",
            "books_0_date": "somewhen",
            "books_0_order": -150,
            "books_1_num": 1,
            "books_1_title": "un",
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        WorkCreateView.as_view()(request)
        a = Antiquarian.objects.get(pk=a.pk)
        self.assertEqual(a.works.exclude(unknown=True).count(), 1)
        w = a.works.first()
        self.assertEqual(Book.objects.filter(work=w, unknown=False).count(), 2)
        self.assertEqual(w.book_set.exclude(unknown=True).count(), 2)

        self.assertIn(w.unknown_book, w.book_set.all())
        bs = w.book_set.all()
        # Books are sorted by unknown, then order, then number
        self.assertTrue(bs.last().unknown)
        self.assertEqual(bs[0].number, 2)
        self.assertEqual(bs[0].subtitle, "deux")
        self.assertEqual(bs[0].order_year, -150)
        self.assertEqual(bs[0].date_range, "somewhen")
        self.assertEqual(bs[1].number, 1)
        self.assertEqual(bs[1].subtitle, "un")


class TestWorkUpdateView(TestCase):
    def test_update(self):
        work = Work.objects.create(name="name")
        url = reverse("work:update", kwargs={"pk": work.pk})
        a1 = Antiquarian.objects.create(name="foo", re_code=1)
        a2 = Antiquarian.objects.create(name="foo", re_code=2)

        data = {
            "antiquarians": [a1.pk],
            "name": "first",
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        work.lock(request.user)

        WorkUpdateView.as_view()(request, pk=work.pk)
        self.assertEqual(a1.works.exclude(unknown=True).count(), 1)
        self.assertEqual(a2.works.exclude(unknown=True).count(), 0)
        self.assertEqual(Work.objects.get(pk=work.pk).name, "first")

        work = Work.objects.create(name="name")
        work.antiquarian_set.add(a1)

        # now transfer this work to another
        data = {"antiquarians": [a2.pk], "name": "other"}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        work.lock(request.user)

        view = WorkUpdateView.as_view()
        # view.form.instance = work

        view(request, pk=work.pk)
        self.assertEqual(a1.works.exclude(unknown=True).count(), 1)
        self.assertEqual(a2.works.exclude(unknown=True).count(), 1)
        self.assertEqual(Work.objects.get(pk=work.pk).name, "other")

    def test_update_with_books(self):
        work = Work.objects.create(name="name2")
        url = reverse("work:update", kwargs={"pk": work.pk})

        data = {
            "antiquarians": [],
            "name": "second",
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        work.lock(request.user)

        WorkUpdateView.as_view()(request, pk=work.pk)

        work = Work.objects.create(name="name")

        # now transfer this work to another
        data = {
            "antiquarians": [],
            "name": "other",
            "books_0_num": 11,
            "books_0_title": "alpha",
            "books_1_num": 12,
            "books_1_title": "beta",
            "books_1_date": "40-10BC",
            "books_1_order": -25,
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        work.lock(request.user)

        view = WorkUpdateView.as_view()
        # view.form.instance = work

        view(request, pk=work.pk)

        bs = work.book_set.exclude(unknown=True)
        self.assertEqual(bs[0].number, 11)
        self.assertEqual(bs[0].subtitle, "alpha")
        self.assertEqual(bs[1].number, 12)
        self.assertEqual(bs[1].subtitle, "beta")
        self.assertEqual(bs[1].order_year, -25)
        self.assertEqual(bs[1].date_range, "40-10BC")


class TestWorkDetailView(TestCase):
    def setUp(self):
        self.user = UserFactory.create()

    def test_ordered_materials(self):
        # the get_ordered_materials function is on the work model but used in the view
        work = Work.objects.create(name="meditations")
        book1 = Book.objects.create(work=work, number=1)
        book2 = Book.objects.create(work=work, number=2)
        unknown_book = work.unknown_book

        f1 = Fragment.objects.create(name="Fragment One")
        FragmentLink.objects.create(
            fragment=f1,
            work=work,
            book=book1,
            definite_work=True,
        )
        f2 = Fragment.objects.create(name="Fragment Two")
        FragmentLink.objects.create(
            fragment=f2,
            work=work,
            book=book2,
            definite_work=False,
        )
        f3 = Fragment.objects.create(name="Fragment Three")
        FragmentLink.objects.create(
            fragment=f3,
            work=work,
            definite_work=False,
        )
        f4 = Fragment.objects.create(name="Fragment Four")
        FragmentLink.objects.create(
            fragment=f4,
            work=work,
            definite_work=True,
        )

        t1 = Testimonium.objects.create(name="Testimonium One")
        TestimoniumLink.objects.create(
            testimonium=t1,
            work=work,
            book=book1,
            definite_work=False,
        )
        t2 = Testimonium.objects.create(name="Testimonium Two")
        TestimoniumLink.objects.create(
            testimonium=t2,
            work=work,
            book=book2,
            definite_work=True,
        )
        t3 = Testimonium.objects.create(name="Testimonium Three")
        TestimoniumLink.objects.create(
            testimonium=t3,
            work=work,
            definite_work=False,
        )
        t4 = Testimonium.objects.create(name="Testimonium Four")
        TestimoniumLink.objects.create(
            testimonium=t4,
            work=work,
            definite_work=True,
        )

        url = reverse("work:detail", kwargs={"pk": work.pk})
        request = RequestFactory().get(url)
        request.user = self.user
        response = WorkDetailView.as_view()(request, pk=work.pk)

        target_materials = {book: {} for book in work.book_set.all()}

        target_materials[book1]["fragments"] = {
            FragmentLink.objects.get(fragment=f1): {
                "linked": f1,
                "definite_antiquarian": False,
                "definite_work": FragmentLink.objects.get(fragment=f1).definite_work,
                "definite_book": False,
                "order": FragmentLink.objects.get(fragment=f1).order,
            },
        }
        target_materials[book2]["fragments"] = {
            FragmentLink.objects.get(fragment=f2): {
                "linked": f2,
                "definite_antiquarian": False,
                "definite_work": FragmentLink.objects.get(fragment=f2).definite_work,
                "definite_book": False,
                "order": FragmentLink.objects.get(fragment=f2).order,
            },
        }
        target_materials[unknown_book]["fragments"] = {
            FragmentLink.objects.get(fragment=f4): {
                "linked": f4,
                "definite_antiquarian": False,
                "definite_work": FragmentLink.objects.get(fragment=f4).definite_work,
                "definite_book": False,
                "order": FragmentLink.objects.get(fragment=f4).order,
            },
            FragmentLink.objects.get(fragment=f3): {
                "linked": f3,
                "definite_antiquarian": False,
                "definite_work": FragmentLink.objects.get(fragment=f3).definite_work,
                "definite_book": False,
                "order": FragmentLink.objects.get(fragment=f3).order,
            },
        }
        target_materials[book1]["testimonia"] = {
            TestimoniumLink.objects.get(testimonium=t1): {
                "linked": t1,
                "definite_antiquarian": False,
                "definite_work": TestimoniumLink.objects.get(
                    testimonium=t1
                ).definite_work,
                "definite_book": False,
                "order": TestimoniumLink.objects.get(testimonium=t1).order,
            },
        }
        target_materials[book2]["testimonia"] = {
            TestimoniumLink.objects.get(testimonium=t2): {
                "linked": t2,
                "definite_antiquarian": False,
                "definite_work": TestimoniumLink.objects.get(
                    testimonium=t2
                ).definite_work,
                "definite_book": False,
                "order": TestimoniumLink.objects.get(testimonium=t2).order,
            },
        }
        target_materials[unknown_book]["testimonia"] = {
            TestimoniumLink.objects.get(testimonium=t4): {
                "linked": t4,
                "definite_antiquarian": False,
                "definite_work": TestimoniumLink.objects.get(
                    testimonium=t4
                ).definite_work,
                "definite_book": False,
                "order": TestimoniumLink.objects.get(testimonium=t4).order,
            },
            TestimoniumLink.objects.get(testimonium=t3): {
                "linked": t3,
                "definite_antiquarian": False,
                "definite_work": TestimoniumLink.objects.get(
                    testimonium=t3
                ).definite_work,
                "definite_book": False,
                "order": TestimoniumLink.objects.get(testimonium=t3).order,
            },
        }
        # ordering the links by order since they're not fetched in that manner
        for book, materials in target_materials.items():
            for material, links in materials.items():
                links_sorted = sorted(links.items(), key=lambda x: x[1]["order"])
                materials[material] = {k: v for k, v in links_sorted}

        assert "ordered_materials" in response.context_data
        assert response.context_data["ordered_materials"] == target_materials
