from uuid import UUID

import mock
import pytest
from django.core.files.images import ImageFile
from django.test import TestCase

from rard.research.models import (CommentableText, Fragment, FragmentImage,
                                  Topic)

pytestmark = pytest.mark.django_db


class TestFragment(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'apparatus_criticus': 'app_criticus',
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(fragment.name, data['name'])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(Fragment._meta.get_field('name').blank)
        self.assertFalse(Fragment._meta.get_field('subtitle').blank)

        # not required on forms
        self.assertTrue(Fragment._meta.get_field('apparatus_criticus').blank)
        self.assertTrue(Fragment._meta.get_field('images').blank)
        self.assertTrue(Fragment._meta.get_field('topics').blank)
        self.assertTrue(Fragment._meta.get_field('definite_works').blank)
        self.assertTrue(Fragment._meta.get_field('possible_works').blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'name',
            'subtitle': 'subtitle',
            'apparatus_criticus': 'app_criticus',
        }
        fragment = Fragment.objects.create(**data)
        self.assertEqual(str(fragment), data['name'])

    def test_primary_key(self):
        # check we are using uuids as primary keys
        fragment = Fragment.objects.create(name='name')
        self.assertIsInstance(fragment.pk, UUID)

    def test_initial_images(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.images.count(), 0)

    def test_initial_topics(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.topics.count(), 0)

    def test_initial_matched_works(self):
        fragment = Fragment.objects.create(name='name')
        self.assertEqual(fragment.definite_works.count(), 0)
        self.assertEqual(fragment.possible_works.count(), 0)

    def test_commentary_created(self):
        fragment = Fragment.objects.create(name='name')
        self.assertIsNotNone(fragment.commentary.pk)
        self.assertEqual(
            CommentableText.objects.get(pk=fragment.commentary.pk),
            fragment.commentary
        )

    def test_commentary_deleted(self):
        fragment = Fragment.objects.create(name='name')
        commentary_pk = fragment.commentary.pk
        fragment.delete()
        with self.assertRaises(CommentableText.DoesNotExist):
            CommentableText.objects.get(pk=commentary_pk)


class TestTopic(TestCase):

    def test_creation_and_pk(self):
        # check we can create and are using uuids as primary keys
        topic = Topic.objects.create(name='name')
        self.assertIsInstance(topic.pk, UUID)

    def test_required_fields(self):
        self.assertFalse(Topic._meta.get_field('name').blank)


class TestFragmentImage(TestCase):
    def setUp(self):
        self.fragment = Fragment.objects.create(name='name')
        self.upload = mock.MagicMock(spec=ImageFile)
        self.upload.name = 'fragment.jpg'

    def test_creation(self):
        data = {
            'title': 'title',
            'description': 'description',
            'credit': 'credit',
            'copyright_status': 'copyright_status',
            'name_and_attribution': 'name_and_attribution',
            'public_release': True,
        }
        image = FragmentImage.objects.create(**data, upload=self.upload)
        for key, val in data.items():
            self.assertEqual(getattr(image, key), val)

    def test_required_fields(self):
        # required on forms
        self.assertFalse(FragmentImage._meta.get_field('title').blank)
        self.assertFalse(FragmentImage._meta.get_field('upload').blank)

        # not required on forms
        self.assertTrue(FragmentImage._meta.get_field('description').blank)
        self.assertTrue(FragmentImage._meta.get_field('credit').blank)
        self.assertTrue(
            FragmentImage._meta.get_field('copyright_status').blank
        )
        self.assertTrue(
            FragmentImage._meta.get_field('name_and_attribution').blank
        )

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'title': 'title',
            'upload': self.upload,
        }
        image = FragmentImage.objects.create(**data)
        self.assertEqual(str(image), data['title'])

    def test_upload_field_name(self):
        image_mock = mock.MagicMock(spec=ImageFile)
        image_mock.name = 'test.jpg'
        image = FragmentImage(upload=image_mock)
        self.assertEqual(image.upload.name, image_mock.name)
