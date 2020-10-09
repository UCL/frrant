import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (CitingWork, Concordance, Fragment,
                                  OriginalText)
from rard.research.views import (ConcordanceCreateView, ConcordanceDeleteView,
                                 ConcordanceListView,
                                 ConcordanceUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestConcordanceViews(TestCase):

    def setUp(self):
        citing_work = CitingWork.objects.create(title='title')
        fragment = Fragment.objects.create(name='name')
        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=citing_work,
        )

    def test_success_urls(self):
        views = [
            ConcordanceCreateView,
            ConcordanceUpdateView,
        ]
        for view_class in views:
            view = view_class()
            request = RequestFactory().get("/")
            request.user = UserFactory.create()

            view.request = request
            view.object = Concordance.objects.create(
                original_text=self.original_text,
                source='source',
                identifier='identifier',
            )

            self.assertEqual(
                view.get_success_url(),
                self.original_text.owner.get_absolute_url()
            )

    def test_delete_success_url(self):
        view = ConcordanceDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Concordance.objects.create(
            original_text=self.original_text,
            source='source',
            identifier='identifier',
        )

        self.assertEqual(
            view.get_success_url(),
            self.original_text.owner.get_absolute_url()
        )

    def test_post_delete_only(self):

        concordance = Concordance.objects.create(
            original_text=self.original_text,
            source='source',
            identifier='identifier',
        )

        url = reverse(
            'concordance:delete',
            kwargs={'pk': concordance.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = ConcordanceDeleteView.as_view()(
            request, pk=concordance.pk
        )
        self.assertEqual(response.status_code, 405)

    def test_create_context_data(self):
        url = reverse(
            'concordance:create',
            kwargs={'pk': self.original_text.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = ConcordanceCreateView.as_view()(
            request, pk=self.original_text.pk
        )

        self.assertEqual(
            response.context_data['original_text'], self.original_text
        )

    def test_update_context_data(self):
        concordance = Concordance.objects.create(
            original_text=self.original_text,
            source='source',
            identifier='identifier',
        )
        url = reverse(
            'concordance:update',
            kwargs={'pk': concordance.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = ConcordanceUpdateView.as_view()(
            request, pk=concordance.pk
        )

        self.assertEqual(
            response.context_data['original_text'], concordance.original_text
        )

    def test_create_view_with_original_text(self):
        url = reverse(
            'concordance:create',
            kwargs={'pk': self.original_text.pk}
        )
        data = {'source': 'source', 'identifier': 'identifier'}

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        # check no concordance previously associated with the original text
        self.assertEqual(
            self.original_text.concordance_set.count(), 0
        )

        ConcordanceCreateView.as_view()(
            request, pk=self.original_text.pk
        )

        # check the new concordance is associated with the original text
        self.assertEqual(
            self.original_text.concordance_set.count(), 1
        )


class TestConcordanceViewPermissions(TestCase):

    def test_permissions(self):

        self.assertIn(
            'research.add_concordance',
            ConcordanceCreateView.permission_required
        )
        self.assertIn(
            'research.change_concordance',
            ConcordanceUpdateView.permission_required
        )
        self.assertIn(
            'research.delete_concordance',
            ConcordanceDeleteView.permission_required
        )
        self.assertIn(
            'research.view_concordance',
            ConcordanceListView.permission_required
        )
