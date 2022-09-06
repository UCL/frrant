from unittest import mock
import pytest
from django.core.files.images import ImageFile
from django.test import TestCase

from rard.research.models import Fragment, Image

pytestmark = pytest.mark.django_db


class TestImage(TestCase):
    def setUp(self):
        self.fragment = Fragment.objects.create(name="name")
        self.upload = mock.MagicMock(spec=ImageFile)
        self.upload.name = "fragment.jpg"

    def test_creation(self):
        data = {
            "title": "title",
            "description": "description",
            "credit": "credit",
            "copyright_status": "copyright_status",
            "name_and_attribution": "name_and_attribution",
            "public_release": True,
        }
        image = Image.objects.create(**data, upload=self.upload)
        for key, val in data.items():
            self.assertEqual(getattr(image, key), val)

    def test_required_fields(self):
        # required on forms
        self.assertFalse(Image._meta.get_field("title").blank)
        self.assertFalse(Image._meta.get_field("upload").blank)

        # not required on forms
        self.assertTrue(Image._meta.get_field("description").blank)
        self.assertTrue(Image._meta.get_field("credit").blank)
        self.assertTrue(Image._meta.get_field("copyright_status").blank)
        self.assertTrue(Image._meta.get_field("name_and_attribution").blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            "title": "title",
            "upload": self.upload,
        }
        image = Image.objects.create(**data)
        self.assertEqual(str(image), data["title"])

    def test_upload_field_name(self):
        image_mock = mock.MagicMock(spec=ImageFile)
        image_mock.name = "test.jpg"
        image = Image(upload=image_mock)
        self.assertEqual(image.upload.name, image_mock.name)
