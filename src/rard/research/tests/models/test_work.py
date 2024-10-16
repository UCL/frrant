import pytest
from django.test import TestCase
from django.urls import reverse

from rard.research.models import (
    Antiquarian,
    Book,
    Fragment,
    Testimonium,
    TextObjectField,
    Work,
)
from rard.research.models.base import FragmentLink, TestimoniumLink
from rard.research.models.work import collate_unknown

pytestmark = pytest.mark.django_db


class TestWork(TestCase):
    def test_creation(self):
        # can create with a name only
        data = {
            "name": "Work Name",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        for key, val in data.items():
            self.assertEqual(getattr(work, key), val)

    def test_ordering(self):
        # ordering should be wrt to the authors of the work
        anta = Antiquarian.objects.create(name="AAA", re_code="aaa")
        antb = Antiquarian.objects.create(name="BBB", re_code="bbb")
        antc = Antiquarian.objects.create(name="CCC", re_code="ccc")

        worka = Work.objects.create(name="aaa")
        workb = Work.objects.create(name="bbb")
        workc = Work.objects.create(name="ccc")

        # 1. check anonymous ordering
        self.assertEqual(
            [w for w in Work.objects.exclude(unknown=True)], [worka, workb, workc]
        )

        antc.works.add(workb)
        # this should now be last with anon works at the start
        self.assertEqual(
            [w for w in Work.objects.exclude(unknown=True)], [worka, workc, workb]
        )

        # the name of the antiquarian should put work c second
        antb.works.add(workc)
        self.assertEqual(
            [w for w in Work.objects.exclude(unknown=True)], [worka, workc, workb]
        )
        # even if we also add antc as an author of workc, as the name of
        # antiquarian antb should govern the order
        antc.works.add(workb)
        self.assertEqual(
            [w for w in Work.objects.exclude(unknown=True)], [worka, workc, workb]
        )

        # now, put worka as a work of anta and this should be first in the
        # list as the name of the antiquarian and then the work should be
        # ahead of the others
        anta.works.add(worka)
        self.assertEqual(
            [w for w in Work.objects.exclude(unknown=True)], [worka, workc, workb]
        )

        # final test - antiquarian name takes precedence
        anta.works.set([workc])
        antb.works.set([workb])
        antc.works.set([worka])
        self.assertEqual(
            [w for w in Work.objects.exclude(unknown=True)], [workc, workb, worka]
        )

    def test_required_fields(self):
        self.assertFalse(Work._meta.get_field("name").blank)
        self.assertTrue(Work._meta.get_field("subtitle").blank)

    def test_display_anonymous(self):
        # the __str__ function should show the name
        data = {
            "name": "Work Name",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        self.assertEqual(str(work), "Anonymous: %s" % data["name"])

    def test_display(self):
        # the __str__ function should show the name
        data = {
            "name": "Work Name",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        antiquarian1 = Antiquarian.objects.create(
            name="John Smith", re_code="smitre001"
        )
        antiquarian1.works.add(work)
        self.assertEqual(str(work), "%s: %s" % (antiquarian1.name, data["name"]))
        # now test mutiple antiquarians
        antiquarian2 = Antiquarian.objects.create(
            name="Joe Bloggs", re_code="blogre002"
        )
        antiquarian2.works.add(work)
        self.assertEqual(
            str(work),
            "%s, %s: %s"
            % (
                antiquarian2.name,
                antiquarian1.name,
                data["name"],
            ),
        )

    def test_work_can_belong_to_multiple_antiquarians(self):
        # works can belong to multiple antiquarians
        data = {
            "name": "Work Name",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        length = 10
        for counter in range(0, length):
            antiquarian = Antiquarian.objects.create(
                name="John Smith", re_code="smitre%03d" % counter
            )
            antiquarian.works.add(work)

        self.assertEqual(work.antiquarian_set.count(), length)

    # def test_disallow_reverse_relator_addition(self):
    #     # to maintain links between antiquarians and fragments when
    #     # works are added and removed, we only support addition of
    #     # works to antiquarians in one direction
    #     antiquarian = Antiquarian.objects.create(
    #         name='John Smith', re_code='smitre001'
    #     )
    #     data = {
    #         'name': 'Work Name',
    #         'subtitle': 'Subtitle',
    #     }
    #     work = Work.objects.create(**data)

    #     # allowed
    #     antiquarian.works.add(work)

    #     antiquarian.works.clear()

    #     # not allowed
    #     with self.assertRaises(IntegrityError):
    #         work.antiquarian_set.add(antiquarian)

    def test_deleting_work_leaves_antiquarian(self):
        # check we are using uuids as primary keys
        data = {
            "name": "Work Name",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        antiquarian = Antiquarian.objects.create(name="John Smith")
        antiquarian.works.add(work)
        antiquarian_pk = antiquarian.pk
        # delete the work
        work.delete()
        # we should still have the antiquarian
        Antiquarian.objects.get(pk=antiquarian_pk)

    def test_order_by_name(self):
        names = [
            "Self Hypnosis for beginners",
            "Fly Fishing",
            "Django development",
            "Creative Writing",
        ]
        for counter, name in enumerate(names):
            Work.objects.create(name=name)

        db_names = []
        for a in Work.objects.all():
            db_names.append(a.name)

        self.assertEqual(db_names, sorted(names))

    def test_get_absolute_url(self):
        data = {
            "name": "Work Name",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        self.assertEqual(
            work.get_absolute_url(), reverse("work:detail", kwargs={"pk": work.pk})
        )

    def test_fragment_methods(self):
        data = {
            "name": "Work Name1",
            "subtitle": "Subtitle",
        }
        work1 = Work.objects.create(**data)
        data = {
            "name": "Work Name2",
            "subtitle": "Subtitle",
        }
        work2 = Work.objects.create(**data)

        # create some fragments
        for i in range(0, 10):
            data = {
                "name": "name{}".format(i),
            }
            Fragment.objects.create(**data)

        # link to work1
        for fragment in Fragment.objects.all():
            FragmentLink.objects.create(
                work=work1,
                fragment=fragment,
                definite_work=True,
            )
        # shoud appear in work1's definite fragments only
        self.assertEqual(
            [x.pk for x in work1.definite_fragments()],
            [x.pk for x in Fragment.objects.all()],
        )
        self.assertEqual(0, len(work1.possible_fragments()))
        # and not in work2's
        self.assertEqual(0, len(work2.definite_fragments()))
        self.assertEqual(0, len(work2.possible_fragments()))

        # make these links possible...
        FragmentLink.objects.update(definite_work=False)
        # shoud appear in work1's possible fragments only
        self.assertEqual(
            [x.pk for x in work1.possible_fragments()],
            [x.pk for x in Fragment.objects.all()],
        )
        self.assertEqual(0, len(work1.definite_fragments()))
        # and not in work2's
        self.assertEqual(0, len(work2.definite_fragments()))
        self.assertEqual(0, len(work2.possible_fragments()))

        # switch all fragment links to work2 and make definite...
        FragmentLink.objects.update(work=work2, definite_work=True)

        # shoud appear in work2's definite fragments only
        self.assertEqual(
            [x.pk for x in work2.definite_fragments()],
            [x.pk for x in Fragment.objects.all()],
        )
        self.assertEqual(0, len(work2.possible_fragments()))
        # and not in work1's
        self.assertEqual(0, len(work1.definite_fragments()))
        self.assertEqual(0, len(work1.possible_fragments()))

        # finally make possible and check...
        FragmentLink.objects.update(definite_work=False)
        # shoud appear in work2's possible fragments only
        self.assertEqual(
            [x.pk for x in work2.possible_fragments()],
            [x.pk for x in Fragment.objects.all()],
        )
        self.assertEqual(0, len(work2.definite_fragments()))
        # and not in work1's
        self.assertEqual(0, len(work1.definite_fragments()))
        self.assertEqual(0, len(work1.possible_fragments()))

    def test_testimonium_methods(self):
        data = {
            "name": "Work Name1",
            "subtitle": "Subtitle",
        }
        work1 = Work.objects.create(**data)
        data = {
            "name": "Work Name2",
            "subtitle": "Subtitle",
        }
        work2 = Work.objects.create(**data)

        # create some testimonia
        for i in range(0, 10):
            data = {
                "name": "name{}".format(i),
            }
            Testimonium.objects.create(**data)

        # link to work1
        for testimonium in Testimonium.objects.all():
            TestimoniumLink.objects.create(
                work=work1,
                testimonium=testimonium,
                definite_work=True,
            )
        # shoud appear in work1's definite testimonia only
        self.assertEqual(
            [x.pk for x in work1.definite_testimonia()],
            [x.pk for x in Testimonium.objects.all()],
        )
        self.assertEqual(0, len(work1.possible_testimonia()))
        # and not in work2's
        self.assertEqual(0, len(work2.definite_testimonia()))
        self.assertEqual(0, len(work2.possible_testimonia()))

        # make these links possible...
        TestimoniumLink.objects.update(definite_work=False)
        # shoud appear in work1's possible testimonia only
        self.assertEqual(
            [x.pk for x in work1.possible_testimonia()],
            [x.pk for x in Testimonium.objects.all()],
        )
        self.assertEqual(0, len(work1.definite_testimonia()))
        # and not in work2's
        self.assertEqual(0, len(work2.definite_testimonia()))
        self.assertEqual(0, len(work2.possible_testimonia()))

        # switch all testimonium links to work2 and make definite...
        TestimoniumLink.objects.update(work=work2, definite_work=True)

        # shoud appear in work2's definite testimonia only
        self.assertEqual(
            [x.pk for x in work2.definite_testimonia()],
            [x.pk for x in Testimonium.objects.all()],
        )
        self.assertEqual(0, len(work2.possible_testimonia()))
        # and not in work1's
        self.assertEqual(0, len(work1.definite_testimonia()))
        self.assertEqual(0, len(work1.possible_testimonia()))

        # finally make possible and check...
        TestimoniumLink.objects.update(definite_work=False)
        # shoud appear in work2's possible testimonia only
        self.assertEqual(
            [x.pk for x in work2.possible_testimonia()],
            [x.pk for x in Testimonium.objects.all()],
        )
        self.assertEqual(0, len(work2.definite_testimonia()))
        # and not in work1's
        self.assertEqual(0, len(work1.definite_testimonia()))
        self.assertEqual(0, len(work1.possible_testimonia()))

    def test_introduction_created_with_work(self):
        data = {
            "name": "workname",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        self.assertIsNotNone(work.introduction.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=work.introduction.pk), work.introduction
        )

    def test_introduction_deleted_with_book(self):
        data = {
            "name": "workname",
            "subtitle": "Subtitle",
        }
        work = Work.objects.create(**data)
        introduction_pk = work.introduction.pk
        work.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=introduction_pk)

    def test_collate_unknown(self):
        data = {
            "name": "workname",
            "subtitle": "Subtitle",
        }
        w = Work.objects.create(**data)
        f = Fragment.objects.create(name="fragment")
        original_unknown = w.unknown_book
        additional_unknown = Book.objects.create(
            unknown=True, subtitle="Unknown Book", work=w
        )
        FragmentLink.objects.create(
            fragment=f,
            work=w,
            book=additional_unknown,
        )

        additional_unknown.save()
        self.assertEqual(w.book_set.filter(unknown=True).count(), 2)
        self.assertEqual(w.antiquarian_work_fragmentlinks.all().count(), 1)
        self.assertEqual(
            w.antiquarian_work_fragmentlinks.first().book, additional_unknown
        )
        collate_unknown(w)
        self.assertEqual(w.book_set.filter(unknown=True).count(), 1)
        self.assertEqual(original_unknown.pk, w.unknown_book.pk)
        self.assertEqual(w.antiquarian_work_fragmentlinks.all().count(), 1)
        self.assertEqual(
            w.antiquarian_work_fragmentlinks.first().book, original_unknown
        )


class TestBook(TestCase):
    def setUp(self):
        self.work = Work.objects.create(name="book_name")

    def test_creation(self):
        # test happy path
        data = {"number": "1", "subtitle": "Subtitle", "work": self.work}
        book = Book.objects.create(**data)
        for key, val in data.items():
            self.assertEqual(getattr(book, key), val)

    def test_work_required(self):
        data_no_work = {
            "number": "1",
            "subtitle": "Subtitle",
        }
        with self.assertRaises(Book.work.RelatedObjectDoesNotExist):
            Book.objects.create(**data_no_work)

    def test_required_fields(self):
        self.assertTrue(Book._meta.get_field("number").blank)
        self.assertTrue(Book._meta.get_field("subtitle").blank)

    def test_get_absolute_url(self):
        # the work url is the absolute url for its book objects
        data = {
            "number": "1",
            "subtitle": "Subtitle",
            "work": self.work,
        }
        book = Book.objects.create(**data)
        self.assertEqual(
            book.get_absolute_url(), reverse("work:detail", kwargs={"pk": self.work.pk})
        )

    def test_display(self):
        # the __str__ function should show the name
        data = {
            "number": "1",
            "subtitle": "Subtitle",
            "work": self.work,
        }
        book = Book.objects.create(**data)
        self.assertEqual(str(book), "Book 1: Subtitle")
        book.number = ""
        self.assertEqual(str(book), "Subtitle")
        book.number = "1"
        book.subtitle = ""
        self.assertEqual(str(book), "Book 1")

    def test_introduction_created_with_book(self):
        data = {
            "number": "1",
            "subtitle": "Subtitle",
            "work": self.work,
        }
        book = Book.objects.create(**data)
        self.assertIsNotNone(book.introduction.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=book.introduction.pk), book.introduction
        )

    def test_introduction_deleted_with_book(self):
        data = {
            "number": "1",
            "subtitle": "Subtitle",
            "work": self.work,
        }
        book = Book.objects.create(**data)
        introduction_pk = book.introduction.pk
        book.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=introduction_pk)
