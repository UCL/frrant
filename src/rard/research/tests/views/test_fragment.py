import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingWork, Fragment
from rard.research.views import FragmentCreateView, FragmentDeleteView
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
