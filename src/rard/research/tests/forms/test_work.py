import pytest
from django.test import TestCase

from rard.research.forms import WorkForm
from rard.research.models import Antiquarian, Work

pytestmark = pytest.mark.django_db


class TestWorkForm(TestCase):
    def test_fields_not_required(self):
        # allow the user to skip either and insist on the backend
        # that at least one of them is filled out
        form = WorkForm()
        self.assertFalse(form.fields["antiquarians"].required)

    def test_antiquarian_queryset(self):

        data = {
            "name": "Work Name",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)

        OWNER_COUNT = 5
        OTHER_COUNT = 3
        for i in range(0, OWNER_COUNT):
            a = Antiquarian.objects.create(name="sdf", re_code="owner%d" % i)
            a.works.add(work)

        for i in range(0, OTHER_COUNT):
            a = Antiquarian.objects.create(name="sdf", re_code="other%d" % i)

        form = WorkForm(instance=work)

        self.assertEqual(form.fields["antiquarians"].initial.count(), OWNER_COUNT)
