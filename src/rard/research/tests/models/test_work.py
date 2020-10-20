import pytest
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from rard.research.models import Antiquarian, Fragment, Work
from rard.research.models.base import FragmentLink

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
            antiquarian = Antiquarian.objects.create(
                name='John Smith', re_code='smitre%03d' % counter
            )
            antiquarian.works.add(work)

        self.assertEqual(work.antiquarian_set.count(), length)

    def test_disallow_reverse_relator_addition(self):
        # to maintain links between antiquarians and fragments when
        # works are added and removed, we only support addition of
        # works to antiquarians in one direction
        antiquarian = Antiquarian.objects.create(
            name='John Smith', re_code='smitre001'
        )
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)

        # allowed
        antiquarian.works.add(work)

        antiquarian.works.clear()

        # not allowed
        with self.assertRaises(IntegrityError):
            work.antiquarian_set.add(antiquarian)

    def test_deleting_work_leaves_antiquarian(self):
        # check we are using uuids as primary keys
        data = {
            'name': 'Work Name',
            'subtitle': 'Subtitle',
        }
        work = Work.objects.create(**data)
        antiquarian = Antiquarian.objects.create(name='John Smith')
        antiquarian.works.add(work)
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

    def test_fragment_methods(self):
        data = {
            'name': 'Work Name1',
            'subtitle': 'Subtitle',
        }
        work1 = Work.objects.create(**data)
        data = {
            'name': 'Work Name2',
            'subtitle': 'Subtitle',
        }
        work2 = Work.objects.create(**data)

        # create some fragments
        for i in range(0, 10):
            data = {
                'name': 'name{}'.format(i),
                'apparatus_criticus': 'app_criticus',
            }
            Fragment.objects.create(**data)

        # link to work1
        for fragment in Fragment.objects.all():
            FragmentLink.objects.create(
                work=work1,
                fragment=fragment,
                definite=True,
            )
        # shoud appear in work1's definite fragments only
        self.assertEqual(
            [x.pk for x in work1.definite_fragments()],
            [x.pk for x in Fragment.objects.all()]
        )
        self.assertEqual(0, len(work1.possible_fragments()))
        # and not in work2's
        self.assertEqual(0, len(work2.definite_fragments()))
        self.assertEqual(0, len(work2.possible_fragments()))

        # make these links possible...
        FragmentLink.objects.update(definite=False)
        # shoud appear in work1's possible fragments only
        self.assertEqual(
            [x.pk for x in work1.possible_fragments()],
            [x.pk for x in Fragment.objects.all()]
        )
        self.assertEqual(0, len(work1.definite_fragments()))
        # and not in work2's
        self.assertEqual(0, len(work2.definite_fragments()))
        self.assertEqual(0, len(work2.possible_fragments()))

        # switch all fragment links to work2 and make definite...
        FragmentLink.objects.update(work=work2, definite=True)

        # shoud appear in work2's definite fragments only
        self.assertEqual(
            [x.pk for x in work2.definite_fragments()],
            [x.pk for x in Fragment.objects.all()]
        )
        self.assertEqual(0, len(work2.possible_fragments()))
        # and not in work1's
        self.assertEqual(0, len(work1.definite_fragments()))
        self.assertEqual(0, len(work1.possible_fragments()))

        # finally make possible and check...
        FragmentLink.objects.update(definite=False)
        # shoud appear in work2's possible fragments only
        self.assertEqual(
            [x.pk for x in work2.possible_fragments()],
            [x.pk for x in Fragment.objects.all()]
        )
        self.assertEqual(0, len(work2.definite_fragments()))
        # and not in work1's
        self.assertEqual(0, len(work1.definite_fragments()))
        self.assertEqual(0, len(work1.possible_fragments()))
