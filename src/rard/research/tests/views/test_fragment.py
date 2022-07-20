import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    AnonymousTopicLink,
    Antiquarian,
    CitingWork,
    Fragment,
    OriginalText,
    Topic,
)
from rard.research.models.base import AppositumFragmentLink, FragmentLink
from rard.research.models.text_object_field import TextObjectField
from rard.research.views import (
    AnonymousFragmentConvertToFragmentView,
    FragmentCreateView,
    FragmentDeleteView,
    FragmentDetailView,
    FragmentListView,
    FragmentUpdateView,
    MoveAnonymousTopicLinkView,
    UnlinkedFragmentConvertToAnonymousView,
)
from rard.users.tests.factories import UserFactory
from rard.utils.convertors import (
    FragmentIsNotConvertible,
    convert_anonymous_fragment_to_fragment,
    convert_unlinked_fragment_to_anonymous_fragment,
)

pytestmark = pytest.mark.django_db


class TestFragmentSuccessUrls(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.citing_work = CitingWork.objects.create(title="title")

    def test_redirect_on_create(self):
        # data for both original text and fragment
        data = {
            "name": "name",
            "apparatus_criticus": "app_criticus",
            "content": "content",
            "reference": "Page 1",
            "reference_order": 1,
            "citing_work": self.citing_work.pk,
            "citing_author": self.citing_work.author.pk,
            "create_object": True,
        }
        # assert no fragments initially
        self.assertEqual(0, Fragment.objects.count())

        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()

        response = FragmentCreateView.as_view()(
            request,
        )
        # we created a fragment
        self.assertEqual(1, Fragment.objects.count())
        created = Fragment.objects.first()
        # check we were redirected to the detail view of that fragment
        self.assertEqual(
            response.url, reverse("fragment:detail", kwargs={"pk": created.pk})
        )

    def test_create_citing_work(self):
        # data for both original text and fragment
        data = {
            "name": "name",
            "apparatus_criticus": "app_criticus",
            "content": "content",
            "reference": "Page 1",
            "reference_order": 1,
            "title": "citing work title",
            "citing_work": self.citing_work.pk,
            "citing_author": self.citing_work.author.pk,
            "create_object": True,
        }
        # assert no fragments initially
        self.assertEqual(0, Fragment.objects.count())
        citing_works_before = CitingWork.objects.count()

        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()

        # call the view
        FragmentCreateView.as_view()(request)

        # we created a fragment
        self.assertEqual(1, Fragment.objects.count())
        # check we did not create a citing work
        self.assertEqual(citing_works_before, CitingWork.objects.count())

    def test_create_bad_data(self):
        # bad data should reset the forms to both be not required
        data = {
            "name": "name",
            "apparatus_criticus": "app_criticus",
            "content": "content",
            "reference": "Page 1",
            "reference_order": 1,
            # we have missing data here
        }
        # assert no fragments initially
        self.assertEqual(0, Fragment.objects.count())
        citing_works_before = CitingWork.objects.count()

        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()

        response = FragmentCreateView.as_view()(
            request,
        )
        # we did not create a fragment
        self.assertEqual(0, Fragment.objects.count())
        # check we did not create a citing work
        self.assertEqual(citing_works_before, CitingWork.objects.count())

        # check the forms here are both not required for the user
        forms = response.context_data["forms"]
        original_text_form = forms["original_text"]

        self.assertTrue(original_text_form.fields["citing_work"].required)

    def test_delete_success_url(self):
        view = FragmentDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Fragment.objects.create(name="some name")

        self.assertEqual(view.get_success_url(), reverse("fragment:list"))

    def test_update_success_url(self):
        view = FragmentUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Fragment.objects.create(name="some name")

        self.assertEqual(
            view.get_success_url(),
            reverse("fragment:detail", kwargs={"pk": view.object.pk}),
        )


class TestFragmentDeleteView(TestCase):
    def test_post_only(self):

        fragment = Fragment.objects.create(name="name")
        url = reverse("fragment:delete", kwargs={"pk": fragment.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = FragmentDeleteView.as_view()(request, pk=fragment.pk)
        self.assertEqual(response.status_code, 405)


class TestFragmentViewPermissions(TestCase):
    def test_permissions(self):

        self.assertIn("research.add_fragment", FragmentCreateView.permission_required)
        self.assertIn(
            "research.change_fragment", FragmentUpdateView.permission_required
        )
        self.assertIn(
            "research.delete_fragment", FragmentDeleteView.permission_required
        )
        self.assertIn("research.view_fragment", FragmentListView.permission_required)
        self.assertIn("research.view_fragment", FragmentDetailView.permission_required)


class TestFragmentConvertViews(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.unlinked_anonymous_fragment = self.create_fragment(
            AnonymousFragment, "uaf"
        )
        self.linked_anonymous_fragment = self.create_fragment(
            AnonymousFragment, "laf", linked=True
        )
        self.unlinked_fragment = self.create_fragment(Fragment, "ufr")
        self.linked_fragment = self.create_fragment(Fragment, "lfr", linked=True)

    def create_fragment(self, model, name, linked=False):
        fragment = model.objects.create(name=name)
        citing_work = CitingWork.objects.create(title="title")
        OriginalText.objects.create(
            owner=fragment, citing_work=citing_work, content="sic semper tyrannis"
        )
        fragment.date_range = "509 BCE - 31 BCE"
        fragment.order_year = -509
        fragment.collection_id = 1
        topic = Topic.objects.create(name=name + " topic")
        fragment.topics.set([topic])
        fragment.commentary = TextObjectField.objects.create(content="hello")
        fragment.save()
        if linked:
            self.add_fragment_link(fragment)
        return fragment

    def add_fragment_link(self, fragment):
        antiquarian = Antiquarian.objects.create(
            name=fragment.name + " antiquarian", re_code=fragment.name
        )
        if isinstance(fragment, Fragment):
            FragmentLink.objects.create(fragment=fragment, antiquarian=antiquarian)
        elif isinstance(fragment, AnonymousFragment):
            AppositumFragmentLink.objects.create(
                anonymous_fragment=fragment, antiquarian=antiquarian
            )

    def test_permissions(self):
        self.assertIn(
            "research.change_anonymousfragment",
            AnonymousFragmentConvertToFragmentView.permission_required,
        )
        self.assertIn(
            "research.change_fragment",
            UnlinkedFragmentConvertToAnonymousView.permission_required,
        )

    def test_raise_error_if_source_is_linked_fragment(self):
        with self.assertRaises(FragmentIsNotConvertible):
            convert_unlinked_fragment_to_anonymous_fragment(self.linked_fragment)

    def test_convert_unlinked_anonymous_fragment_to_fragment(self):
        source_pk = self.unlinked_anonymous_fragment.pk
        new_fragment = convert_anonymous_fragment_to_fragment(
            self.unlinked_anonymous_fragment
        )
        with self.assertRaises(ObjectDoesNotExist):
            AnonymousFragment.objects.get(pk=source_pk)
        self.assertEqual(new_fragment.topics.all()[0].name, "uaf topic")
        self.assertEqual(
            new_fragment.original_texts.all()[0].content, "sic semper tyrannis"
        )
        self.assertEqual(new_fragment.date_range, "509 BCE - 31 BCE")
        self.assertEqual(new_fragment.commentary.content, "hello")

    def test_convert_linked_anonymous_fragment_to_fragment(self):
        new_fragment = convert_anonymous_fragment_to_fragment(
            self.linked_anonymous_fragment
        )
        new_fragment_link = new_fragment.antiquarian_fragmentlinks.all()[0]
        self.assertEqual(new_fragment_link.antiquarian.name, "laf antiquarian")

    def test_convert_unlinked_fragment_to_anonymous_fragment(self):
        source_pk = self.unlinked_fragment.pk
        new_fragment = convert_unlinked_fragment_to_anonymous_fragment(
            self.unlinked_fragment
        )
        with self.assertRaises(ObjectDoesNotExist):
            Fragment.objects.get(pk=source_pk)
        self.assertEqual(new_fragment.topics.all()[0].name, "ufr topic")
        self.assertEqual(
            new_fragment.original_texts.all()[0].content, "sic semper tyrannis"
        )
        self.assertEqual(new_fragment.date_range, "509 BCE - 31 BCE")
        self.assertEqual(new_fragment.commentary.content, "hello")

    def test_converted_unlinked_has_correct_order(self):
        """Make sure newly created anonymous fragment has the correct order
        value."""
        ufr_topic = Topic.objects.get(name="ufr topic")
        ufr_topic.move_to(0)  # Give unlinked fragment's topic first place
        new_fragment = convert_unlinked_fragment_to_anonymous_fragment(
            self.unlinked_fragment
        )
        new_fragment.save()
        self.assertEqual(ufr_topic.order, 0)
        self.assertEqual(new_fragment.order, 0)


class TestMoveAnonymousTopicLinkView(TestCase):
    def setUp(self):
        # Create 3 anon frags, 1 of which is an apposita
        af1 = AnonymousFragment.objects.create(name="af1")
        af2 = AnonymousFragment.objects.create(name="af2")
        af3 = AnonymousFragment.objects.create(name="af3")
        ant = Antiquarian.objects.create()
        AppositumFragmentLink.objects.create(anonymous_fragment=af1, antiquarian=ant)
        # Create topic and add all 3 anon frags
        top1 = Topic.objects.create(name="top1")
        af1.topics.add(top1)
        af2.topics.add(top1)
        af3.topics.add(top1)

    def test_move_anon_fragment_link_up(self):
        top1 = Topic.objects.get(name="top1")
        af1 = AnonymousFragment.objects.get(name="af1")
        af2 = AnonymousFragment.objects.get(name="af2")
        af3 = AnonymousFragment.objects.get(name="af3")
        atl1 = AnonymousTopicLink.objects.filter(fragment=af1, topic=top1).first()
        atl2 = AnonymousTopicLink.objects.filter(fragment=af2, topic=top1).first()
        atl3 = AnonymousTopicLink.objects.filter(fragment=af3, topic=top1).first()
        self.assertEqual([atl1.order, atl2.order, atl3.order], [0, 1, 2])
        data = {"move_to": 1, "topic_id": top1.id, "anonymoustopiclink_id": atl3.id}
        view = MoveAnonymousTopicLinkView.as_view()
        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()
        response = view(
            request,
        )
        self.assertEqual(response.status_code, 200)
        atl1.refresh_from_db()
        atl2.refresh_from_db()
        atl3.refresh_from_db()
        self.assertEqual([atl1.order, atl2.order, atl3.order], [0, 2, 1])

    def test_move_anon_fragment_link_down(self):
        top1 = Topic.objects.get(name="top1")
        af1 = AnonymousFragment.objects.get(name="af1")
        af2 = AnonymousFragment.objects.get(name="af2")
        af3 = AnonymousFragment.objects.get(name="af3")
        atl1 = AnonymousTopicLink.objects.filter(fragment=af1, topic=top1).first()
        atl2 = AnonymousTopicLink.objects.filter(fragment=af2, topic=top1).first()
        atl3 = AnonymousTopicLink.objects.filter(fragment=af3, topic=top1).first()
        self.assertEqual([atl1.order, atl2.order, atl3.order], [0, 1, 2])
        data = {"move_to": 2, "topic_id": top1.id, "anonymoustopiclink_id": atl2.id}
        view = MoveAnonymousTopicLinkView.as_view()
        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()
        response = view(
            request,
        )
        self.assertEqual(response.status_code, 200)
        atl1.refresh_from_db()
        atl2.refresh_from_db()
        atl3.refresh_from_db()
        self.assertEqual([atl1.order, atl2.order, atl3.order], [0, 2, 1])
