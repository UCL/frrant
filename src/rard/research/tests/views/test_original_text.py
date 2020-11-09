import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingWork, Fragment, OriginalText
from rard.research.views import (FragmentOriginalTextCreateView,
                                 OriginalTextDeleteView,
                                 OriginalTextUpdateView,
                                 TestimoniumOriginalTextCreateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestOriginalTextCreateViews(TestCase):

    def setUp(self):
        self.citing_work = CitingWork.objects.create(title='title')

    def test_update_success_url(self):
        view = OriginalTextUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        fragment = Fragment.objects.create(name='name')
        text = OriginalText.objects.create(
            owner=fragment,
            citing_work=self.citing_work,
        )

        view.request = request
        view.object = text
        self.assertEqual(
            view.get_success_url(),
            fragment.get_absolute_url()
        )

    def test_create_get_parent_and_success_url(self):
        view = FragmentOriginalTextCreateView()
        fragment = Fragment.objects.create(name='name')

        request = RequestFactory().get("/")
        request.user = UserFactory.create()
        view.request = request
        view.kwargs = {'pk': fragment.pk}

        fragment.lock(request.user)

        self.assertEqual(
            view.get_parent_object(),
            fragment
        )
        self.assertEqual(
            view.get_success_url(),
            fragment.get_absolute_url()
        )

    def test_creation_post(self):
        # data for both original text and fragment
        data = {
            'content': 'content',
            'citing_work': self.citing_work.pk,
        }
        # assert no original texts initially
        self.assertEqual(0, OriginalText.objects.count())

        fragment = Fragment.objects.create(name='name')
        url = reverse(
            'fragment:create_original_text',
            kwargs={'pk': fragment.pk}
        )

        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        fragment.lock(request.user)

        FragmentOriginalTextCreateView.as_view()(
            request, pk=fragment.pk
        )
        # we created an original text
        self.assertEqual(1, OriginalText.objects.count())
        created = OriginalText.objects.first()
        # check its owner
        self.assertEqual(created.owner, fragment)

    def test_delete_success_url(self):
        view = OriginalTextDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        fragment = Fragment.objects.create(name='name')

        fragment.lock(request.user)

        text = OriginalText.objects.create(
            owner=fragment,
            citing_work=self.citing_work,
        )

        view.request = request
        view.object = text

        self.assertEqual(
            view.get_success_url(),
            fragment.get_absolute_url()
        )


class TestOriginalTextDeleteView(TestCase):

    def setUp(self):
        self.citing_work = CitingWork.objects.create(title='title')

    def test_post_only(self):

        fragment = Fragment.objects.create(name='name')
        text = OriginalText.objects.create(
            owner=fragment,
            citing_work=self.citing_work,
        )
        url = reverse(
            'fragment:delete_original_text',
            kwargs={'pk': text.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()

        fragment.lock(request.user)

        response = OriginalTextDeleteView.as_view()(
            request, pk=text.pk
        )
        self.assertEqual(response.status_code, 405)


class TestOriginalTextViewsDispatch(TestCase):

    def setUp(self):
        self.citing_work = CitingWork.objects.create(title='title')
        fragment = Fragment.objects.create(name='name')
        self.user = UserFactory.create()
        fragment.lock(self.user)

        self.original_text = OriginalText.objects.create(
            owner=fragment,
            citing_work=self.citing_work,
        )

    def test_update_delete_create_top_level_object(self):

        # dispatch method creates an attribute used by the
        # locking mechanism so here we ensure it is created
        request = RequestFactory().post('/')
        request.user = self.user

        for view_class in (OriginalTextUpdateView, OriginalTextDeleteView,):
            view = view_class()
            view.request = request
            view.kwargs = {'pk': self.original_text.pk}
            view.dispatch(request)
            self.assertEqual(view.parent_object, self.original_text.owner)


class TestOriginalTextViewPermissions(TestCase):

    def test_permissions(self):
        self.assertIn(
            'research.add_originaltext',
            FragmentOriginalTextCreateView.permission_required
        )
        self.assertIn(
            'research.change_fragment',
            FragmentOriginalTextCreateView.permission_required
        )
        self.assertIn(
            'research.add_originaltext',
            TestimoniumOriginalTextCreateView.permission_required
        )
        self.assertIn(
            'research.change_testimonium',
            TestimoniumOriginalTextCreateView.permission_required
        )
        self.assertIn(
            'research.change_originaltext',
            OriginalTextUpdateView.permission_required
        )
        self.assertIn(
            'research.delete_originaltext',
            OriginalTextDeleteView.permission_required
        )
