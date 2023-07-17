import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingWork, Fragment, OriginalText, Translation
from rard.research.views import (
    TranslationCreateView,
    TranslationDeleteView,
    TranslationUpdateView,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTranslationCreateView(TestCase):
    def setUp(self):
        citing_work = CitingWork.objects.create(title="title")
        fragment = Fragment.objects.create(name="name")
        self.user = UserFactory.create()
        fragment.lock(self.user)
        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=citing_work,
        )

    def test_success_url(self):
        view = TranslationCreateView()
        request = RequestFactory().get("/")
        request.user = self.user

        translation = Translation.objects.create(original_text=self.original_text)
        view.request = request
        view.kwargs = {"pk": self.original_text.pk}

        # this is usually done in dispatch
        view.top_level_object = self.original_text.owner

        self.assertEqual(
            view.get_success_url(), translation.original_text.owner.get_absolute_url()
        )

    def test_context_data(self):
        url = reverse(
            "fragment:create_translation", kwargs={"pk": self.original_text.pk}
        )
        request = RequestFactory().get(url)
        request.user = self.user
        response = TranslationCreateView.as_view()(request, pk=self.original_text.pk)

        self.assertEqual(response.context_data["original_text"], self.original_text)

    def test_post_creation(self):
        data = {
            "original_text": self.original_text,
            "translated_text": "translated_text",
            "translator_name": "translator_name",
        }
        # assert no translations initially
        self.assertEqual(0, Translation.objects.count())

        url = reverse(
            "fragment:create_translation", kwargs={"pk": self.original_text.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = self.user

        TranslationCreateView.as_view()(request, pk=self.original_text.pk)
        # we created an object
        self.assertEqual(1, Translation.objects.count())
        created = Translation.objects.first()
        self.assertEqual(created.original_text, self.original_text)

    def test_translated_text_required(self):
        data = {
            "original_text": self.original_text,
            "translator_name": "translator_name",
        }
        # assert no translations initially
        self.assertEqual(0, Translation.objects.count())

        url = reverse(
            "fragment:create_translation", kwargs={"pk": self.original_text.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = self.user

        TranslationCreateView.as_view()(request, pk=self.original_text.pk)
        # no object created
        self.assertEqual(0, Translation.objects.count())

    def test_translator_name_required(self):
        data = {
            "original_text": self.original_text,
            "translated_text": "translated_text",
        }
        # assert no translations initially
        self.assertEqual(0, Translation.objects.count())

        url = reverse(
            "fragment:create_translation", kwargs={"pk": self.original_text.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = self.user

        TranslationCreateView.as_view()(request, pk=self.original_text.pk)
        # no object created
        self.assertEqual(0, Translation.objects.count())


class TestTranslationViewsDispatch(TestCase):
    def setUp(self):
        self.citing_work = CitingWork.objects.create(title="title")
        fragment = Fragment.objects.create(name="name")
        self.user = UserFactory.create()
        fragment.lock(self.user)

        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=self.citing_work,
        )

    def test_update_delete_create_top_level_object(self):
        # dispatch method creates an attribute used by the
        # locking mechanism so here we ensure it is created
        request = RequestFactory().post("/")
        request.user = self.user

        translation = Translation.objects.create(original_text=self.original_text)

        for view_class in (
            TranslationUpdateView,
            TranslationDeleteView,
        ):
            view = view_class()
            view.request = request
            view.kwargs = {"pk": translation.pk}
            view.dispatch(request)
            self.assertEqual(view.top_level_object, self.original_text.owner)


class TestTranslationUpdateView(TestCase):
    def setUp(self):
        citing_work = CitingWork.objects.create(title="title")
        fragment = Fragment.objects.create(name="name")
        self.user = UserFactory.create()
        fragment.lock(self.user)
        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=citing_work,
        )

    def test_success_url(self):
        view = TranslationUpdateView()
        request = RequestFactory().get("/")
        request.user = self.user

        translation = Translation.objects.create(original_text=self.original_text)

        view.request = request
        view.object = translation

        # this is usually done in dispatch
        view.top_level_object = self.original_text.owner

        self.assertEqual(
            view.get_success_url(), translation.original_text.owner.get_absolute_url()
        )

    def test_context_data(self):
        translation = Translation.objects.create(original_text=self.original_text)
        url = reverse("fragment:update_translation", kwargs={"pk": translation.pk})
        request = RequestFactory().get(url)
        request.user = self.user
        response = TranslationUpdateView.as_view()(request, pk=translation.pk)

        self.assertEqual(
            response.context_data["original_text"], translation.original_text
        )


class TestTranslationDeleteView(TestCase):
    def setUp(self):
        citing_work = CitingWork.objects.create(title="title")
        fragment = Fragment.objects.create(name="name")
        self.user = UserFactory.create()
        fragment.lock(self.user)
        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=citing_work,
        )

    def test_post_only(self):
        translation = Translation.objects.create(original_text=self.original_text)
        url = reverse("fragment:delete_translation", kwargs={"pk": translation.pk})
        request = RequestFactory().get(url)
        request.user = self.user
        response = TranslationDeleteView.as_view()(request, pk=translation.pk)
        self.assertEqual(response.status_code, 405)

    def test_success_url(self):
        view = TranslationDeleteView()
        request = RequestFactory().get("/")
        request.user = self.user

        translation = Translation.objects.create(original_text=self.original_text)

        view.request = request
        view.object = translation

        # this is usually done in dispatch
        view.top_level_object = self.original_text.owner

        self.assertEqual(
            view.get_success_url(), translation.original_text.owner.get_absolute_url()
        )


class TestTranslationViewPermissions(TestCase):
    def test_permissions(self):
        self.assertIn(
            "research.add_translation", TranslationCreateView.permission_required
        )
        self.assertIn(
            "research.delete_translation", TranslationDeleteView.permission_required
        )
        self.assertIn(
            "research.change_translation", TranslationUpdateView.permission_required
        )
