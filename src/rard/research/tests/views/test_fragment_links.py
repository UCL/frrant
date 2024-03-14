import pytest
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import AnonymousFragment, Antiquarian, Fragment, Work
from rard.research.models.base import FragmentLink
from rard.research.views import (
    AddAppositumAnonymousLinkView,
    FragmentAddWorkLinkView,
    RemoveAnonymousAppositumLinkView,
    RemoveAppositumFragmentLinkView,
    RemoveFragmentLinkView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestFragmentAddWorkLinkView(TestCase):
    def test_success_url(self):
        view = FragmentAddWorkLinkView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.fragment = Fragment.objects.create(name="name")

        self.assertEqual(
            view.get_success_url(),
            reverse("fragment:detail", kwargs={"pk": view.fragment.pk}),
        )

    def test_create_link_post(self):
        fragment = Fragment.objects.create(name="name")
        antiquarian = Antiquarian.objects.create(name="name", re_code=1)
        work = Work.objects.create(name="name")
        antiquarian.works.add(work)
        url = reverse("fragment:add_work_link", kwargs={"pk": fragment.pk})
        data = {"antiquarian": antiquarian.pk, "work": work.pk}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()
        fragment.lock(request.user)

        self.assertEqual(FragmentLink.objects.count(), 0)
        FragmentAddWorkLinkView.as_view()(request, pk=fragment.pk)
        self.assertEqual(FragmentLink.objects.count(), 1)
        link = FragmentLink.objects.first()
        self.assertEqual(link.fragment, fragment)
        self.assertEqual(link.work, work)

    def test_context_data(self):
        fragment = Fragment.objects.create(name="name")
        work = Work.objects.create(name="name")
        url = reverse("fragment:add_work_link", kwargs={"pk": fragment.pk})
        data = {"work": work.pk}
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()
        fragment.lock(request.user)

        response = FragmentAddWorkLinkView.as_view()(request, pk=fragment.pk)
        self.assertEqual(response.context_data["work"], work)
        self.assertEqual(response.context_data["fragment"], fragment)

    def test_bad_data(self):
        fragment = Fragment.objects.create(name="name")
        work = Work.objects.create(name="name")
        url = reverse("fragment:add_work_link", kwargs={"pk": fragment.pk})
        data = {"work": work.pk + 100}  # bad value
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()
        fragment.lock(request.user)

        with self.assertRaises(Http404):
            FragmentAddWorkLinkView.as_view()(request, pk=fragment.pk)

    def test_permission_required(self):
        self.assertIn(
            "research.change_fragment", FragmentAddWorkLinkView.permission_required
        )


class TestFragmentRemoveWorkLinkView(TestCase):
    def test_success_url(self):
        fragment = Fragment.objects.create(name="name")
        work = Work.objects.create(name="name")
        FragmentLink.objects.create(work=work, fragment=fragment)

        view = RemoveFragmentLinkView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()
        fragment.lock(request.user)

        view.request = request
        view.fragment = fragment

        self.assertEqual(
            view.get_success_url(),
            reverse("fragment:detail", kwargs={"pk": fragment.pk}),
        )

    def test_delete_link_post(self):
        """If there's more than one link, a link can be removed as normal"""
        fragment = Fragment.objects.create(name="name")
        work = Work.objects.create(name="name")
        link1 = FragmentLink.objects.create(work=work, fragment=fragment)
        link2 = FragmentLink.objects.create(work=work, fragment=fragment)

        request = RequestFactory().post("/")
        request.user = UserFactory.create()
        fragment.lock(request.user)

        self.assertEqual(FragmentLink.objects.count(), 2)
        RemoveFragmentLinkView.as_view()(request, pk=link1.pk)
        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertEqual(FragmentLink.objects.first(), link2)

    def test_reassign_to_unknown(self):
        """If only one link is left, it should be reassigned to unknown work/book on delete
        to retain the link to the antiquarian"""

        antiquarian = Antiquarian.objects.create(name="name", re_code="re_code")
        fragment = Fragment.objects.create(name="name")
        work = Work.objects.create(name="name", antiquarian=antiquarian)
        link = FragmentLink.objects.create(
            work=work, fragment=fragment, antiquarian=antiquarian
        )
        link.definite_work = True
        link.definite_book = True
        link.save()

        request = RequestFactory().post("/")
        request.user = UserFactory.create()
        fragment.lock(request.user)

        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertTrue(FragmentLink.objects.first().definite_work)
        self.assertTrue(FragmentLink.objects.first().definite_book)
        RemoveFragmentLinkView.as_view()(request, pk=link.pk)
        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertTrue(FragmentLink.objects.first().work.unknown)
        self.assertFalse(FragmentLink.objects.first().definite_work)
        self.assertFalse(FragmentLink.objects.first().definite_book)

    def test_remove_all_links(self):
        """when the 'remove all links' button is clicked
        the request should contain information about the antiquarian
        and delete all links for that antiquarian and fragment"""
        antiquarian = Antiquarian.objects.create(name="name", re_code="re_code")
        fragment = Fragment.objects.create(name="name")
        work = Work.objects.create(name="name")
        link1 = FragmentLink.objects.create(
            work=work, fragment=fragment, antiquarian=antiquarian
        )
        link2 = FragmentLink.objects.create(
            work=work, fragment=fragment, antiquarian=antiquarian
        )

        link1.save()
        link2.save()

        request = RequestFactory().post("/", data={"antiquarian_request": fragment.pk})
        request.user = UserFactory.create()
        fragment.lock(request.user)

        self.assertEqual(FragmentLink.objects.count(), 2)
        RemoveFragmentLinkView.as_view()(request, pk=antiquarian.pk)
        self.assertEqual(FragmentLink.objects.count(), 0)

    def test_permission_required(self):
        self.assertIn(
            "research.change_fragment", RemoveFragmentLinkView.permission_required
        )


class TestAnonymousFragmentAppositaViews(TestCase):
    def setUp(self):
        self.af1 = AnonymousFragment.objects.create(name="af1")
        self.af2 = AnonymousFragment.objects.create(name="af2")
        self.af3 = AnonymousFragment.objects.create(name="af3")
        self.af3.anonymous_fragments.add(self.af2)

    def test_add_apposita_to_anonymous_fragment(self):
        """Use AddAppositumAnonymousLinkView to add one anonymous fragment (af1)
        as an apposita to another (af2)"""
        url = reverse("anonymous_fragment:link_anonymous", kwargs={"pk": self.af1.pk})
        view = AddAppositumAnonymousLinkView.as_view()
        data = {"anonymous_fragment": self.af2.pk}
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()
        self.af1.lock(request.user)
        self.assertEqual(self.af1.anonymous_fragments.count(), 0)
        view(request, pk=self.af1.pk)
        self.assertEqual(self.af1.anonymous_fragments.count(), 1)
        self.assertQuerysetEqual(self.af1.anonymous_fragments.all(), [self.af2])

    def test_unlink_apposita_and_anonymous_fragment(self):
        """Use RemoveAppositumFragmentLinkView to remove an existing appositum link between
        an anonymous fragment (af2) and its appositum (af3)"""
        self.assertEqual(self.af3.anonymous_fragments.count(), 1)
        url = reverse(
            "anonymous_fragment:unlink_anonymous_apposita",
            kwargs={"pk": self.af2.pk, "link_pk": self.af3.pk},
        )
        view = RemoveAnonymousAppositumLinkView.as_view()
        request = RequestFactory().post(url)
        request.user = UserFactory.create()
        self.af3.lock(request.user)
        view(request, pk=self.af2.pk, link_pk=self.af3.pk)
        self.assertEqual(self.af3.anonymous_fragments.count(), 0)


class TestUnlinkedFragmentAppositaViews(TestCase):
    def setUp(self):
        self.af1 = AnonymousFragment.objects.create(name="af1")
        self.uf1 = Fragment.objects.create(name="uf1")
        self.uf1.apposita.add(self.af1)

    def test_unlink_apposita_from_unlinked_fragment(self):
        """Use RemoveAppositumFragmentLinkView to remove an unlinked
        fragment's apposita"""
        self.assertEqual(self.af1.fragments.count(), 1)
        url = reverse(
            "anonymous_fragment:unlink_fragment_apposita",
            kwargs={"pk": self.af1.pk, "frag_pk": self.uf1.pk},
        )
        view = RemoveAppositumFragmentLinkView.as_view()
        request = RequestFactory().post(url)
        request.user = UserFactory.create()
        self.af1.lock(request.user)
        view(request, pk=self.af1.pk, frag_pk=self.uf1.pk)
        self.assertEqual(self.af1.fragments.count(), 0)
