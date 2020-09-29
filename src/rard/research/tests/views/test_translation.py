import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (CitingWork, Fragment, OriginalText,
                                  Translation)
from rard.research.views import (TranslationCreateView, TranslationDeleteView,
                                 TranslationUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTranslationCreateView(TestCase):

    def setUp(self):
        citing_work = CitingWork.objects.create(title='title')
        fragment = Fragment.objects.create(name='name')
        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=citing_work,
        )

    def test_success_url(self):
        view = TranslationCreateView()
        request = RequestFactory().get('/')
        request.user = UserFactory.create()

        translation = Translation.objects.create(
            original_text=self.original_text
        )
        view.request = request
        view.kwargs = {'pk': self.original_text.pk}

        self.assertEqual(
            view.get_success_url(),
            translation.original_text.owner.get_detail_url()
        )

    def test_context_data(self):
        url = reverse(
            'fragment:create_translation',
            kwargs={'pk': self.original_text.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TranslationCreateView.as_view()(
            request, pk=self.original_text.pk
        )

        self.assertEqual(
            response.context_data['original_text'], self.original_text
        )

    def test_post_creation(self):

        data = {
            'original_text': self.original_text,
            'translated_text': 'translated_text',
            'translator_name': 'translator_name',
        }
        # assert no translations initially
        self.assertEqual(0, Translation.objects.count())

        url = reverse(
            'fragment:create_translation',
            kwargs={'pk': self.original_text.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        TranslationCreateView.as_view()(
            request, pk=self.original_text.pk
        )
        # we created an object
        self.assertEqual(1, Translation.objects.count())
        created = Translation.objects.first()
        self.assertEqual(created.original_text, self.original_text)

    def test_translated_text_required(self):

        data = {
            'original_text': self.original_text,
            'translator_name': 'translator_name',
        }
        # assert no translations initially
        self.assertEqual(0, Translation.objects.count())

        url = reverse(
            'fragment:create_translation',
            kwargs={'pk': self.original_text.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        TranslationCreateView.as_view()(
            request, pk=self.original_text.pk
        )
        # no object created
        self.assertEqual(0, Translation.objects.count())

    def test_translator_name_required(self):

        data = {
            'original_text': self.original_text,
            'translated_text': 'translated_text',
        }
        # assert no translations initially
        self.assertEqual(0, Translation.objects.count())

        url = reverse(
            'fragment:create_translation',
            kwargs={'pk': self.original_text.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        TranslationCreateView.as_view()(
            request, pk=self.original_text.pk
        )
        # no object created
        self.assertEqual(0, Translation.objects.count())


class TestTranslationUpdateView(TestCase):

    def setUp(self):
        citing_work = CitingWork.objects.create(title='title')
        fragment = Fragment.objects.create(name='name')
        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=citing_work,
        )

    def test_success_url(self):
        view = TranslationUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        translation = Translation.objects.create(
            original_text=self.original_text
        )

        view.request = request
        view.object = translation

        self.assertEqual(
            view.get_success_url(),
            translation.original_text.owner.get_detail_url()
        )

    def test_context_data(self):
        translation = Translation.objects.create(
            original_text=self.original_text
        )
        url = reverse(
            'fragment:update_translation',
            kwargs={'pk': translation.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TranslationUpdateView.as_view()(
            request, pk=translation.pk
        )

        self.assertEqual(
            response.context_data['original_text'], translation.original_text
        )


class TestTranslationDeleteView(TestCase):

    def setUp(self):
        citing_work = CitingWork.objects.create(title='title')
        fragment = Fragment.objects.create(name='name')
        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=citing_work,
        )

    def test_post_only(self):
        translation = Translation.objects.create(
            original_text=self.original_text
        )
        url = reverse(
            'fragment:delete_translation',
            kwargs={'pk': translation.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = TranslationDeleteView.as_view()(
            request, pk=translation.pk
        )
        self.assertEqual(response.status_code, 405)

    def test_success_url(self):
        view = TranslationDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        translation = Translation.objects.create(
            original_text=self.original_text
        )

        view.request = request
        view.object = translation

        self.assertEqual(
            view.get_success_url(),
            translation.original_text.owner.get_detail_url()
        )
