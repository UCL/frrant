import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingWork, Fragment
from rard.research.views import (FragmentCreateView, FragmentDeleteView,
                                 FragmentUpdateView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestFragmentSuccessUrls(TestCase):

    def setUp(self):
        self.user = UserFactory.create()
        self.citing_work = CitingWork.objects.create(title='title')

    def test_redirect_on_create(self):
        # data for both original text and fragment
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
            'content': 'content',
            'citing_work': self.citing_work.pk,
        }
        # assert no fragments initially
        self.assertEqual(0, Fragment.objects.count())

        request = RequestFactory().post('/', data=data)
        request.user = UserFactory.create()

        response = FragmentCreateView.as_view()(
            request,
        )
        # we created a fragment
        self.assertEqual(1, Fragment.objects.count())
        created = Fragment.objects.first()
        # check we were redirected to the detail view of that fragment
        self.assertEqual(
            response.url,
            reverse('fragment:detail', kwargs={'pk': created.pk})
        )

    def test_create_citing_work(self):
        # data for both original text and fragment
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
            'content': 'content',
            'new_citing_work': 'true',
            'title': 'citing work title'
        }
        # assert no fragments initially
        self.assertEqual(0, Fragment.objects.count())
        citing_works_before = CitingWork.objects.count()

        request = RequestFactory().post('/', data=data)
        request.user = UserFactory.create()

        # call the view
        FragmentCreateView.as_view()(request)

        # we created a fragment
        self.assertEqual(1, Fragment.objects.count())
        # check we also created a citing work
        self.assertEqual(citing_works_before + 1, CitingWork.objects.count())

    def test_create_bad_data(self):
        # bad data should reset the forms to both be not required
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
            'content': 'content',
            'new_citing_work': 'true',
            # we have missing data here
        }
        # assert no fragments initially
        self.assertEqual(0, Fragment.objects.count())
        citing_works_before = CitingWork.objects.count()

        request = RequestFactory().post('/', data=data)
        request.user = UserFactory.create()

        response = FragmentCreateView.as_view()(
            request,
        )
        # we did not create a fragment
        self.assertEqual(0, Fragment.objects.count())
        # check we did not create a citing work
        self.assertEqual(citing_works_before, CitingWork.objects.count())

        # check the forms here are both not required for the user
        forms = response.context_data['forms']
        citing_work_form = forms['new_citing_work']
        original_text_form = forms['original_text']

        self.assertFalse(original_text_form.fields['citing_work'].required)
        self.assertFalse(citing_work_form.fields['new_citing_work'].required)
        self.assertFalse(citing_work_form.fields['author'].required)
        self.assertFalse(citing_work_form.fields['title'].required)
        self.assertFalse(citing_work_form.fields['edition'].required)

    def test_delete_success_url(self):
        view = FragmentDeleteView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Fragment.objects.create(name='some name')

        self.assertEqual(
            view.get_success_url(),
            reverse('fragment:list')
        )

    def test_update_success_url(self):
        view = FragmentUpdateView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.object = Fragment.objects.create(name='some name')

        self.assertEqual(
            view.get_success_url(),
            reverse('fragment:detail', kwargs={'pk': view.object.pk})
        )


class TestFragmentDeleteView(TestCase):
    def test_post_only(self):

        fragment = Fragment.objects.create(name='name')
        url = reverse(
            'fragment:delete',
            kwargs={'pk': fragment.pk}
        )
        request = RequestFactory().get(url)
        request.user = UserFactory.create()
        response = FragmentDeleteView.as_view()(
            request, pk=fragment.pk
        )
        self.assertEqual(response.status_code, 405)
