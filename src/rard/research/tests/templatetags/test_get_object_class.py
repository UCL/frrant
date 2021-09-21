import pytest
from django.test import TestCase

from rard.research.models import Antiquarian, Fragment, Testimonium, Topic, Work
from rard.research.templatetags.get_object_class import get_object_class

pytestmark = pytest.mark.django_db


class TestGetObjectClass(TestCase):
    def test_model_values(self):
        for obj_class in (Antiquarian, Fragment, Testimonium, Topic, Work):
            obj = obj_class()
            self.assertEqual(get_object_class(obj), obj_class.__name__)

    def test_ignore_builtin(self):
        for obj in (1, "hi", 3.2, None):
            self.assertEqual(get_object_class(obj), "")

    def test_ignore_builtin_class_types(self):
        for x in (int, str, float):
            self.assertEqual(get_object_class(x), "")
