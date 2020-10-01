import pytest
from django.test import TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, Work

pytestmark = pytest.mark.django_db


class TestWork(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        for key, val in data.items():
            self.assertEqual(getattr(work, key), val)

    def test_required_fields(self):
        self.assertFalse(Work._meta.get_field('name').blank)
        self.assertTrue(Work._meta.get_field('subtitle').blank)

    def test_display_anonymous(self):
        # the __str__ function should show the name
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        self.assertEqual(str(work), '%s: Anonymous' % data['name'])

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        antiquarian1 = Antiquarian.objects.create(
            name='John Smith', re_code='smitre001'
        )
        antiquarian1.works.add(work)
        self.assertEqual(
            str(work), '%s: %s' % (data['name'], antiquarian1.name)
        )
        antiquarian2 = Antiquarian.objects.create(
            name='Joe Bloggs', re_code='blogre002'
        )
        antiquarian2.works.add(work)
        self.assertEqual(
            str(work), '%s: %s, %s' % (
                data['name'],
                antiquarian2.name, antiquarian1.name,
            )
        )

    def test_work_can_belong_to_multiple_antiquarians(self):
        # works can belong to multiple antiquarians
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        length = 10
        for counter in range(0, length):
            work.antiquarian_set.create(
                name='John Smith', re_code='smitre%03d' % counter
            )

        self.assertEqual(work.antiquarian_set.count(), length)

    def test_deleting_work_leaves_antiquarian(self):
        # check we are using uuids as primary keys
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        antiquarian = work.antiquarian_set.create(name='John Smith')
        antiquarian_pk = antiquarian.pk
        # delete the work
        work.delete()
        # we should still have the antiquarian
        Antiquarian.objects.get(pk=antiquarian_pk)

    def test_order_by_name(self):
        names = [
            'Self Hypnosis for beginners',
            'Fly Fishing',
            'Django development',
            'Creative Writing',
        ]
        for counter, name in enumerate(names):
            Work.objects.create(
                name=name
            )

        db_names = []
        for a in Work.objects.all():
            db_names.append(a.name)

        self.assertEqual(db_names, sorted(names))

    def test_get_absolute_url(self):
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        self.assertEqual(
            work.get_absolute_url(),
            reverse('work:detail', kwargs={'pk': work.pk})
        )
