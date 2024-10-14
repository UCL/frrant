import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    ApparatusCriticusItem,
    CitingWork,
    Concordance,
    Fragment,
    OriginalText,
    Reference,
    Testimonium,
    TextObjectField,
    Translation,
)
from rard.research.views import (
    TestimoniumCreateView,
    TestimoniumDeleteView,
    TestimoniumDetailView,
    TestimoniumListView,
    TestimoniumUpdateView,
    duplicate_fragment,
)
from rard.users.tests.factories import UserFactory
from rard.utils.convertors import (
    convert_testimonium_to_unlinked_fragment,
    convert_unlinked_fragment_to_testimonium,
)

pytestmark = pytest.mark.django_db


class TestTestimoniumSuccessUrls(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.citing_work = CitingWork.objects.create(title="title")

    def test_redirect_on_create(self):
        # data for both original text and testimonia
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
            "create_object": True,
        }
        # assert no testimonia initially
        self.assertEqual(0, Testimonium.objects.count())

        request = RequestFactory().post("/", data=data)
        request.user = UserFactory.create()

        response = TestimoniumCreateView.as_view()(
            request,
        )
        # we created an object
        self.assertEqual(1, Testimonium.objects.count())
        created = Testimonium.objects.first()
        # check we were redirected to the detail view of that object
        self.assertEqual(
            response.url, reverse("testimonium:detail", kwargs={"pk": created.pk})
        )

    def test_delete_success_url(self):
        view = TestimoniumDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Testimonium.objects.create(name="some name")

        self.assertEqual(view.get_success_url(), reverse("testimonium:list"))

    def test_update_success_url(self):
        view = TestimoniumUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Testimonium.objects.create(name="some name")

        self.assertEqual(
            view.get_success_url(),
            reverse("testimonium:detail", kwargs={"pk": view.object.pk}),
        )


class TestTestimoniumDeleteView(TestCase):
    def test_post_only(self):
        testimonium = Testimonium.objects.create(name="name")
        url = reverse("testimonium:delete", kwargs={"pk": testimonium.pk})
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TestimoniumDeleteView.as_view()(request, pk=testimonium.pk)
        self.assertEqual(response.status_code, 405)


class TestTestimoniumViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn(
            "research.add_testimonium", TestimoniumCreateView.permission_required
        )
        self.assertIn(
            "research.change_testimonium", TestimoniumUpdateView.permission_required
        )
        self.assertIn(
            "research.delete_testimonium", TestimoniumDeleteView.permission_required
        )
        self.assertIn(
            "research.view_testimonium", TestimoniumListView.permission_required
        )
        self.assertIn(
            "research.view_testimonium", TestimoniumDetailView.permission_required
        )


class TestTestimoniumDuplicationView(TestCase):
    def setUp(self):
        self.cw = CitingWork.objects.create(title="citing work title")
        self.tes = Testimonium.objects.create(name="test testimonium")
        self.ot = OriginalText.objects.create(
            owner=self.tes,
            content="Original Text test",
            citing_work=self.cw,
            reference_order="reference order",
        )
        self.con = Concordance.objects.create(
            original_text=self.ot, source="tester", identifier="123"
        )
        self.apc = ApparatusCriticusItem.objects.create(
            parent=self.ot, content="critical test", object_id=23
        )
        self.tr = Translation.objects.create(
            translated_text="translation of text", original_text=self.ot
        )
        self.ref = Reference.objects.create(editor="test", original_text=self.ot)

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

    def test_testimonium_duplication(self):
        url = reverse(
            "testimonium:duplicate",
            kwargs={"pk": self.tes.pk, "model_name": "testimonium"},
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = duplicate_fragment(request, pk=self.tes.pk, model_name="testimonium")

        duplicate_pk = response.url.split("/")[-2]
        duplicate_frag = Fragment.objects.get(pk=duplicate_pk)
        duplicate_ot = duplicate_frag.original_texts.first()
        duplicate_ref = duplicate_ot.references.first()
        duplicate_apc = duplicate_ot.apparatus_criticus_items.first()
        duplicate_con = duplicate_ot.concordances.first()
        duplicate_tr = Translation.objects.filter(original_text=duplicate_ot).first()

        self.compare_model_objects(self.tes, duplicate_frag)
        self.compare_model_objects(self.ot, duplicate_ot)
        self.compare_model_objects(self.ref, duplicate_ref)
        self.compare_model_objects(self.apc, duplicate_apc)
        self.compare_model_objects(self.con, duplicate_con)
        self.compare_model_objects(self.tr, duplicate_tr)
        self.assertIn(duplicate_frag, self.tes.duplicates_list)
        self.assertIn(self.tes, duplicate_frag.duplicates_list)


class TestTestimoniumConversionViews(TestCase):
    def setUp(self):
        self.unlinked_fragment = self.create_fragment(Fragment, "ufr")
        self.testimonium = self.create_fragment(Testimonium, "tes")

    def create_fragment(self, model, name):
        fragment = model.objects.create(name=name)
        citing_work = CitingWork.objects.create(title="title")
        OriginalText.objects.create(
            owner=fragment, citing_work=citing_work, content="sic semper tyrannis"
        )
        fragment.date_range = "509 BCE - 31 BCE"
        fragment.order_year = -509
        fragment.collection_id = 1
        fragment.commentary = TextObjectField.objects.create(content="hello")
        fragment.save()
        return fragment

    def test_convert_unlinked_fragment_to_testimonium(self):
        source_pk = self.unlinked_fragment.pk
        new_testimonium = convert_unlinked_fragment_to_testimonium(
            self.unlinked_fragment
        )
        with self.assertRaises(ObjectDoesNotExist):
            Fragment.objects.get(pk=source_pk)
        self.assertEqual(
            new_testimonium.original_texts.first().content, "sic semper tyrannis"
        )
        self.assertEqual(new_testimonium.collection_id, 1)
        self.assertEqual(new_testimonium.commentary.content, "hello")

    def test_convert_testimonium_to_unlinked_fragment(self):
        source_pk = self.testimonium.pk
        new_fragment = convert_testimonium_to_unlinked_fragment(self.testimonium)
        with self.assertRaises(ObjectDoesNotExist):
            Testimonium.objects.get(pk=source_pk)
        self.assertEqual(
            new_fragment.original_texts.first().content, "sic semper tyrannis"
        )
        self.assertEqual(new_fragment.commentary.content, "hello")
