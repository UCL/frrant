import pytest
from django.http.response import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import CitingWork, Fragment, Work
from rard.research.models.base import FragmentLink
from rard.research.views import (FragmentAddWorkLinkView,
                                 FragmentRemoveWorkLinkView)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestFragmentAddWorkLinkView(TestCase):

    def test_success_url(self):
        view = FragmentAddWorkLinkView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.fragment = Fragment.objects.create(name='name')

        self.assertEqual(
            view.get_success_url(),
            reverse('fragment:detail', kwargs={'pk': view.fragment.pk})
        )

    def test_create_link_post(self):

        fragment = Fragment.objects.create(name='name')
        work = Work.objects.create(name='name')
        url = reverse(
            'fragment:add_work_link',
            kwargs={'pk': fragment.pk}
        )
        data = {
            'work': work.pk
        }
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory.create()

        self.assertEqual(FragmentLink.objects.count(), 0)
        response = FragmentAddWorkLinkView.as_view()(
            request, pk=fragment.pk
        )
        self.assertEqual(FragmentLink.objects.count(), 1)
        link = FragmentLink.objects.first()
        self.assertEqual(link.fragment, fragment)
        self.assertEqual(link.work, work)


    def test_context_data(self):
        fragment = Fragment.objects.create(name='name')
        work = Work.objects.create(name='name')
        url = reverse(
            'fragment:add_work_link',
            kwargs={'pk': fragment.pk}
        )
        data = {
            'work': work.pk
        }
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()
        response = FragmentAddWorkLinkView.as_view()(
            request, pk=fragment.pk
        )
        self.assertEqual(
            response.context_data['work'], work
        )
        self.assertEqual(
            response.context_data['fragment'], fragment
        )

    def test_bad_data(self):

        fragment = Fragment.objects.create(name='name')
        work = Work.objects.create(name='name')
        url = reverse(
            'fragment:add_work_link',
            kwargs={'pk': fragment.pk}
        )
        data = {
            'work': work.pk + 100  # bad value
        }
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory.create()
        with self.assertRaises(Http404):
            response = FragmentAddWorkLinkView.as_view()(
                request, pk=fragment.pk
            )


class TestFragmentRemoveWorkLinkView(TestCase):

    def test_success_url(self):
        fragment = Fragment.objects.create(name='name')
        work = Work.objects.create(name='name')
        link = FragmentLink.objects.create(work=work, fragment=fragment)

        view = FragmentRemoveWorkLinkView()
        request = RequestFactory().get("/")
        request.user = UserFactory.create()

        view.request = request
        view.fragment = fragment

        self.assertEqual(
            view.get_success_url(),
            reverse('fragment:detail', kwargs={'pk': fragment.pk})
        )

    def test_delete_link_post(self):

        fragment = Fragment.objects.create(name='name')
        work = Work.objects.create(name='name')
        link = FragmentLink.objects.create(work=work, fragment=fragment)
        
        request = RequestFactory().post('/')
        request.user = UserFactory.create()

        self.assertEqual(FragmentLink.objects.count(), 1)
        response = FragmentRemoveWorkLinkView.as_view()(
            request, pk=fragment.pk, linked_pk=work.pk
        )
        self.assertEqual(FragmentLink.objects.count(), 0)
