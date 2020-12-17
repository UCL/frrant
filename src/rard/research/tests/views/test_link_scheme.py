from unittest import skip

import pytest
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, Fragment
from rard.research.models.base import FragmentLink
from rard.research.views import AntiquarianDetailView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@skip('Indexing scheme has changed')
class TestLinkSchemeViews(TestCase):

    def test_post_up_down(self):

        a = Antiquarian.objects.create(name='name', re_code='name')
        fragment = Fragment.objects.create(name='name')
        link1 = FragmentLink.objects.create(fragment=fragment, antiquarian=a)
        link2 = FragmentLink.objects.create(fragment=fragment, antiquarian=a)

        self.assertEqual(0, link1.order)
        self.assertEqual(1, link2.order)

        data = {
            'link_id': link1.pk,
            'object_type': 'fragment',
            'down': 'down'
        }

        url = reverse('antiquarian:detail', kwargs={'pk': a.pk})

        user = UserFactory.create()
        request = RequestFactory().post(url, data=data)
        request.user = user

        response = AntiquarianDetailView.as_view()(
            request, pk=a.pk
        )
        self.assertEqual(response.status_code, 302)

        # refetch from db
        link1 = FragmentLink.objects.get(pk=link1.pk)
        link2 = FragmentLink.objects.get(pk=link2.pk)

        # check it was moved
        self.assertEqual(1, link1.order)
        self.assertEqual(0, link2.order)

        # now move it back up
        data = {
            'link_id': link1.pk,
            'object_type': 'fragment',
            'up': 'up'
        }

        request = RequestFactory().post(url, data=data)
        request.user = user

        response = AntiquarianDetailView.as_view()(
            request, pk=a.pk
        )
        self.assertEqual(response.status_code, 302)

        # refetch from db
        link1 = FragmentLink.objects.get(pk=link1.pk)
        link2 = FragmentLink.objects.get(pk=link2.pk)

        # check it was moved up
        self.assertEqual(0, link1.order)
        self.assertEqual(1, link2.order)

        # handle bad link ID gracefully
        data['link_id'] = '12345'
        request = RequestFactory().post(url, data=data)
        request.user = user

        response = AntiquarianDetailView.as_view()(
            request, pk=a.pk
        )
        self.assertEqual(response.status_code, 302)

        # refetch from db
        link1 = FragmentLink.objects.get(pk=link1.pk)
        link2 = FragmentLink.objects.get(pk=link2.pk)

        # check it was not moved
        self.assertEqual(0, link1.order)
        self.assertEqual(1, link2.order)
