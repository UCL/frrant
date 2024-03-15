import pytest
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    AnonymousTopicLink,
    Antiquarian,
    ApparatusCriticusItem,
    CitingAuthor,
    CitingWork,
    Concordance,
    Fragment,
    OriginalText,
    Reference,
    TextObjectField,
    Topic,
    Translation,
)
from rard.research.models.base import AppositumFragmentLink, FragmentLink
from rard.research.views import (
    AnonymousFragmentConvertToFragmentView,
    AnonymousFragmentListView,
    FragmentCreateView,
    FragmentDeleteView,
    FragmentDetailView,
    FragmentListView,
    FragmentUpdateView,
    MoveAnonymousTopicLinkView,
    UnlinkedFragmentConvertToAnonymousView,
    duplicate_fragment,
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
            "apparatus_criticus": "app_criticus",
            "content": "content",
            "reference_order": 1,
            "citing_work": self.citing_work.pk,
            "citing_author": self.citing_work.author.pk,
            "create_object": True,
            "references-TOTAL_FORMS": 1,
            "references-INITIAL_FORMS": 0,
            "references-MIN_NUM_FORMS": 0,
            "references-MAX_NUM_FORMS": 1000,
            "references-0-id": "",
            "references-0-original_text": "",
            "references-0-editor": "geoff",
            "references-0-reference_position": "1.2.3",
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
            "apparatus_criticus": "app_criticus",
            "content": "content",
            "reference_order": 1,
            "citing_work": self.citing_work.pk,
            "citing_author": self.citing_work.author.pk,
            "create_object": True,
            "references-TOTAL_FORMS": 1,
            "references-INITIAL_FORMS": 0,
            "references-MIN_NUM_FORMS": 0,
            "references-MAX_NUM_FORMS": 1000,
            "references-0-id": "",
            "references-0-original_text": "",
            "references-0-editor": "geoff",
            "references-0-reference_position": "1.2.3",
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

    def test_duplication_success_url(self):
        original_fragment = Fragment.objects.create(name="some name")

        # Simulate the behavior of the duplicate_fragment view
        request = RequestFactory().get("/")
        request.user = UserFactory.create()
        response = duplicate_fragment(
            request, original_fragment.pk, model_name="fragment"
        )
        duplicate_pk = response.url.split("/")[-2]

        expected_url = reverse("fragment:detail", kwargs={"pk": duplicate_pk})

        self.assertEqual(response.url, expected_url)
        self.assertEqual(response.status_code, 302)


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
        # Some more anonymous fragments to be apposita
        self.af1 = self.create_fragment(AnonymousFragment, "af1")
        self.af2 = self.create_fragment(AnonymousFragment, "af2")
        # Create an unlinked fragment with apposita
        self.unlinked_fragment_with_apposita = self.create_fragment(Fragment, "ufr_app")
        self.unlinked_fragment_with_apposita.apposita.add(self.af1)
        # Create an anonymous fragment with apposita
        self.anon_fragment_with_apposita = self.create_fragment(
            AnonymousFragment, "afr_app"
        )
        self.anon_fragment_with_apposita.anonymous_apposita.add(self.af2)

        self.mentioning_fragment = self.create_fragment(Fragment, "f mentioner")
        self.mentioning_fragment.commentary = TextObjectField.objects.create(
            content=(
                f"<p><span class='mention' data-denotation-char='@'' "
                f"data-id={self.unlinked_fragment.pk} "
                f"data-index='0' data-target='Fragment' "
                f"data-value='{self.unlinked_fragment.get_display_name()}'><span contenteditable='false'>"
                f"<span class='ql-mention-denotation-char'>@</span>{self.unlinked_fragment.get_display_name()}"
                f"</span></span> </p>"
            )
        )
        self.mentioning_fragment.commentary.save()

        self.mentioning_anonymous_fragment = self.create_fragment(
            Fragment, "af mentioner"
        )
        self.mentioning_anonymous_fragment.commentary = TextObjectField.objects.create(
            content=(
                f"<p><span class='mention' data-denotation-char='@'' "
                f"data-id={self.unlinked_anonymous_fragment.pk} "
                f"data-index='0' data-target='AnonymousFragment' "
                f"data-value='{self.unlinked_anonymous_fragment.get_display_name()}'><span contenteditable='false'>"
                f"<span class='ql-mention-denotation-char'>@</span>{self.unlinked_anonymous_fragment.get_display_name()}"
                f"</span></span> </p>"
            )
        )
        self.mentioning_anonymous_fragment.commentary.save()

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

    def test_converted_unlinked_retains_mentions(self):
        """Make sure newly created anon frag has the same mentions as original"""
        mentioned_in = self.unlinked_fragment.mentioned_in_list
        self.assertIn(
            self.unlinked_fragment.get_display_name(),
            self.mentioning_fragment.commentary.content,
        )
        new_fragment = convert_unlinked_fragment_to_anonymous_fragment(
            self.unlinked_fragment
        )
        new_fragment.save()
        self.mentioning_fragment.commentary.refresh_from_db()
        self.assertEqual(mentioned_in, new_fragment.mentioned_in_list)
        self.assertNotIn(
            self.unlinked_fragment.get_display_name(),
            self.mentioning_fragment.commentary.content,
        )
        self.assertIn(str(new_fragment.pk), self.mentioning_fragment.commentary.content)
        self.assertIn(
            new_fragment.get_display_name(), self.mentioning_fragment.commentary.content
        )
        self.assertIn(self.mentioning_fragment, new_fragment.mentioned_in_list)

    def test_converted_anonymous_retains_mentions(self):
        """Make sure newly created frag has the same mentions as original"""
        mentioned_in = self.unlinked_anonymous_fragment.mentioned_in_list
        self.assertIn(
            self.unlinked_anonymous_fragment.get_display_name(),
            self.mentioning_anonymous_fragment.commentary.content,
        )
        new_fragment = convert_anonymous_fragment_to_fragment(
            self.unlinked_anonymous_fragment
        )
        new_fragment.save()

        self.mentioning_anonymous_fragment.commentary.refresh_from_db()
        self.assertEqual(mentioned_in, new_fragment.mentioned_in_list)
        self.assertNotIn(
            self.unlinked_anonymous_fragment.get_display_name(),
            self.mentioning_anonymous_fragment.commentary.content,
        )
        self.assertIn(
            str(new_fragment.pk), self.mentioning_anonymous_fragment.commentary.content
        )
        self.assertIn(
            new_fragment.get_display_name(),
            self.mentioning_anonymous_fragment.commentary.content,
        )
        self.assertIn(
            self.mentioning_anonymous_fragment, new_fragment.mentioned_in_list
        )

    def test_converted_anonymous_fragment_maintains_apposita(self):
        """If the original anonymous fragment had any apposita, those
        apposita should belong to the newly created unlinked fragment"""
        new_unlinked_fragment = convert_anonymous_fragment_to_fragment(
            self.anon_fragment_with_apposita
        )
        # self.af2 was apposita to anon fragment, should now be apposita to new fragment
        self.assertQuerysetEqual(new_unlinked_fragment.apposita.all(), [self.af2])

    def test_converted_unlinked_fragment_maintains_apposita(self):
        """If the original unlinked fragment had any apposita, those
        apposita should belong to the newly created anonymous fragment"""
        new_anon_fragment = convert_unlinked_fragment_to_anonymous_fragment(
            self.unlinked_fragment_with_apposita
        )
        # self.af1 was originally apposita to the unlinked fragment
        self.assertQuerysetEqual(new_anon_fragment.anonymous_apposita.all(), [self.af1])


class TestMoveAnonymousTopicLinkView(TestCase):
    def setUp(self):
        # Create 3 anon frags, 1 of which is an apposita
        self.af1 = AnonymousFragment.objects.create(name="af1")
        self.af2 = AnonymousFragment.objects.create(name="af2")
        self.af3 = AnonymousFragment.objects.create(name="af3")
        ant = Antiquarian.objects.create()
        AppositumFragmentLink.objects.create(
            anonymous_fragment=self.af1, antiquarian=ant
        )
        # Create topic and add all 3 anon frags
        self.top1 = Topic.objects.create(name="top1")
        self.af1.topics.add(self.top1)
        self.af2.topics.add(self.top1)
        self.af3.topics.add(self.top1)

    def test_move_anon_fragment_link_up(self):
        atl1 = AnonymousTopicLink.objects.filter(
            fragment=self.af1, topic=self.top1
        ).first()
        atl2 = AnonymousTopicLink.objects.filter(
            fragment=self.af2, topic=self.top1
        ).first()
        atl3 = AnonymousTopicLink.objects.filter(
            fragment=self.af3, topic=self.top1
        ).first()
        self.assertEqual([atl1.order, atl2.order, atl3.order], [0, 1, 2])
        data = {
            "move_to": 1,
            "topic_id": self.top1.id,
            "anonymoustopiclink_id": atl3.id,
        }
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
        atl1 = AnonymousTopicLink.objects.filter(
            fragment=self.af1, topic=self.top1
        ).first()
        atl2 = AnonymousTopicLink.objects.filter(
            fragment=self.af2, topic=self.top1
        ).first()
        atl3 = AnonymousTopicLink.objects.filter(
            fragment=self.af3, topic=self.top1
        ).first()
        self.assertEqual([atl1.order, atl2.order, atl3.order], [0, 1, 2])
        data = {
            "move_to": 2,
            "topic_id": self.top1.id,
            "anonymoustopiclink_id": atl2.id,
        }
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

    def test_move_apposita_raises_error(self):
        atl1 = AnonymousTopicLink.objects.filter(
            fragment=self.af1, topic=self.top1
        ).first()
        self.assertEqual(atl1.order, 0)
        data = {
            "move_to": 1,
            "topic_id": self.top1.id,
            "anonymoustopiclink_id": atl1.id,
        }
        view = MoveAnonymousTopicLinkView.as_view()
        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()
        msg = "Apposita cannot be reordered within a topic"
        self.assertRaises(BadRequest, view, request, msg=msg)

    def test_topic_not_found_raises_404(self):
        atl2 = AnonymousTopicLink.objects.filter(
            fragment=self.af2, topic=self.top1
        ).first()
        data = {"move_to": 2, "topic_id": 99, "anonymoustopiclink_id": atl2.id}
        view = MoveAnonymousTopicLinkView.as_view()
        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()
        self.assertRaises(Http404, view, request)

    def test_link_not_found_raises_404(self):
        data = {"move_to": 2, "topic_id": self.top1.id, "anonymoustopiclink_id": 99}
        view = MoveAnonymousTopicLinkView.as_view()
        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()
        self.assertRaises(Http404, view, request)


class TestOrderAnonymousFragmentListView(TestCase):
    def setUp(self):
        # create two citing works
        self.ca1 = CitingAuthor.objects.create(name="Alice", order_name="Alice")
        self.ca2 = CitingAuthor.objects.create(name="Bob", order_name="Bob")
        self.cw1 = CitingWork.objects.create(title="cw1", author=self.ca1)
        self.cw2 = CitingWork.objects.create(title="cw2", author=self.ca2)

        # Create 3 anon frags
        self.af1 = AnonymousFragment.objects.create(name="af1")
        self.af2 = AnonymousFragment.objects.create(name="af2")
        self.af3 = AnonymousFragment.objects.create(name="af3")

        # Create original texts
        self.ot1 = OriginalText.objects.create(
            content="content",
            citing_work=self.cw1,
            owner=self.af1,
            reference_order="7.1.1",
        )
        self.ot2 = OriginalText.objects.create(
            content="more content",
            citing_work=self.cw2,
            owner=self.af2,
            reference_order="3.5.7",
        )
        self.ot3 = OriginalText.objects.create(
            content="more content",
            citing_work=self.cw2,
            owner=self.af3,
            reference_order="6.5.7",
        )
        self.ot4 = OriginalText.objects.create(
            content="more content",
            citing_work=self.cw2,
            owner=self.af3,
            reference_order="2.5.8",
        )
        self.af1.original_texts.add(self.ot1)
        self.af2.original_texts.add(self.ot2)
        self.af3.original_texts.add(self.ot4, self.ot3)

        # Create topic and add all 3 anon frags
        self.top1 = Topic.objects.create(name="top1")
        self.af1.topics.add(self.top1)
        self.af2.topics.add(self.top1)
        self.af3.topics.add(self.top1)

        # get related AnonymousTopicLinks
        self.aftl1 = AnonymousTopicLink.objects.get(fragment=self.af1)
        self.aftl2 = AnonymousTopicLink.objects.get(fragment=self.af2)
        self.aftl3 = AnonymousTopicLink.objects.get(fragment=self.af3)

    def test_context_data_default_ordering(self):
        url = reverse("anonymous_fragment:list")
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = AnonymousFragmentListView.as_view()(request)

        self.assertEqual(response.context_data["display_order"], "by_topic")

    def test_context_data_reference_ordering(self):
        url = reverse("anonymous_fragment:list")
        data = {
            "display_order": "by_reference",
        }
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()

        response = AnonymousFragmentListView.as_view()(request)

        self.assertEqual(response.context_data["display_order"], "by_reference")

    def test_compare_orders(self):
        url = reverse("anonymous_fragment:list")

        data = {
            "display_order": "by_reference",
        }
        standard_request = RequestFactory().get(url)
        standard_request.user = UserFactory.create()
        standard_response = AnonymousFragmentListView.as_view()(standard_request)

        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()
        response = AnonymousFragmentListView.as_view()(request)

        self.assertNotEqual(
            list(standard_response.context_data["object_list"].all()),
            list(response.context_data["object_list"].all()),
        )

        self.assertQuerysetEqual(
            response.context_data["object_list"],
            [self.aftl1, self.aftl3, self.aftl2, self.aftl3],
        )


class TestFragmentDuplicationView(TestCase):
    def setUp(self):
        self.cw = CitingWork.objects.create(title="citing work title")
        self.topic = Topic.objects.create(name="topic1")
        self.frag = Fragment.objects.create(name="test fragment")
        self.frag.topics.add(self.topic)
        self.anonfrag = AnonymousFragment.objects.create(name="test anonfragment")
        self.anonfrag.topics.add(self.topic)
        self.ot = OriginalText.objects.create(
            owner=self.frag,
            content="Original Text test",
            citing_work=self.cw,
            reference_order="reference order",
        )
        self.ot2 = OriginalText.objects.create(
            owner=self.anonfrag,
            content="Original Text2 test",
            citing_work=self.cw,
            reference_order="reference order",
        )
        self.con = Concordance.objects.create(
            original_text=self.ot, source="tester", identifier="123"
        )
        self.con = Concordance.objects.create(
            original_text=self.ot2, source="tester", identifier="123"
        )
        self.apc = ApparatusCriticusItem.objects.create(
            parent=self.ot, content="critical test", object_id=23
        )
        self.apc2 = ApparatusCriticusItem.objects.create(
            parent=self.ot2, content="critical test", object_id=23
        )
        self.tr = Translation.objects.create(
            translated_text="translation of text", original_text=self.ot
        )
        self.tr2 = Translation.objects.create(
            translated_text="translation of text", original_text=self.ot2
        )
        self.ref = Reference.objects.create(editor="test", original_text=self.ot)
        self.ref2 = Reference.objects.create(editor="test", original_text=self.ot2)

    def compare_model_objects(self, original, duplicate):
        for field in original._meta.fields:
            if field.name in [
                "id",
                "created",
                "modified",
                "commentary",
                "plain_commentary",
                "object_id",
                "original_text",
                "order",
                "model",
            ]:
                continue
            if field.is_relation and getattr(original, field.name):
                # If the field is a relation, compare the related objects
                related_original = getattr(original, field.name)
                related_duplicate = getattr(duplicate, field.name)
                self.compare_model_objects(related_original, related_duplicate)
            else:
                # For regular fields or null relations, compare their values
                value1 = getattr(original, field.name)
                value2 = getattr(duplicate, field.name)
                self.assertEqual(value1, value2)

    def test_fragment_duplication(self):
        url = reverse(
            "fragment:duplicate", kwargs={"pk": self.frag.pk, "model_name": "fragment"}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = duplicate_fragment(request, pk=self.frag.pk, model_name="fragment")

        duplicate_pk = response.url.split("/")[-2]
        duplicate_frag = Fragment.objects.get(pk=duplicate_pk)
        duplicate_ot = duplicate_frag.original_texts.first()
        duplicate_ref = duplicate_ot.references.first()
        duplicate_apc = duplicate_ot.apparatus_criticus_items.first()
        duplicate_con = duplicate_ot.concordances.first()
        duplicate_tr = Translation.objects.filter(original_text=duplicate_ot).first()

        self.compare_model_objects(self.frag, duplicate_frag)
        self.assertEqual(
            list(self.frag.topics.all()), list(duplicate_frag.topics.all())
        )
        self.compare_model_objects(self.ot, duplicate_ot)
        self.compare_model_objects(self.ref, duplicate_ref)
        self.compare_model_objects(self.apc, duplicate_apc)
        self.compare_model_objects(self.con, duplicate_con)
        self.compare_model_objects(self.tr, duplicate_tr)

    def test_anonymous_fragment_duplication(self):
        url = reverse(
            "anonymous_fragment:duplicate",
            kwargs={"pk": self.anonfrag.pk, "model_name": "anonymousfragment"},
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = duplicate_fragment(
            request, pk=self.anonfrag.pk, model_name="anonymousfragment"
        )

        duplicate_pk = response.url.split("/")[-2]
        duplicate_frag = Fragment.objects.get(pk=duplicate_pk)
        duplicate_ot = duplicate_frag.original_texts.first()
        duplicate_ref = duplicate_ot.references.first()

        duplicate_apc = duplicate_ot.apparatus_criticus_items.first()
        duplicate_con = duplicate_ot.concordances.first()
        duplicate_tr = Translation.objects.filter(original_text=duplicate_ot).first()

        self.compare_model_objects(self.anonfrag, duplicate_frag)
        self.assertEqual(
            list(self.anonfrag.topics.all()), list(duplicate_frag.topics.all())
        )
        self.compare_model_objects(self.ot2, duplicate_ot)
        self.compare_model_objects(self.ref, duplicate_ref)
        self.compare_model_objects(self.apc, duplicate_apc)
        self.compare_model_objects(self.con, duplicate_con)
        self.compare_model_objects(self.tr, duplicate_tr)
