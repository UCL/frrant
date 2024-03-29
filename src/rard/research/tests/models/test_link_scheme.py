import pytest
from django.test import TestCase

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    Book,
    Fragment,
    Testimonium,
    Work,
)
from rard.research.models.base import (
    AppositumFragmentLink,
    FragmentLink,
    TestimoniumLink,
)

pytestmark = pytest.mark.django_db


class TestAntiquarianLinkScheme(TestCase):
    def test_querysets(self):
        # tinkering with ordering of querysets can cause sideeffects
        # with duplicate entries etcs
        # in the results so we do a sanity check here
        NUM = 20
        stub = "name{}"
        for model_class in (Fragment, Testimonium):
            for i in range(0, NUM):
                data = {
                    "name": stub.format(i),
                }
                model_class.objects.create(**data)

            self.assertEqual(model_class.objects.count(), NUM)
            for i, obj in enumerate(model_class.objects.all()):
                self.assertEqual(obj.name, stub.format(i))

    def test_linked_property(self):
        a = Antiquarian.objects.create(name="name", re_code="name")
        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)
        link = FragmentLink.objects.create(fragment=fragment, antiquarian=a)
        self.assertEqual(link.linked, fragment)
        self.assertEqual(
            a.fragments.count(), FragmentLink.objects.filter(antiquarian=a).count()
        )
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a)):
            self.assertEqual(count, link.order)

    def test_display_name(self):
        a = Antiquarian.objects.create(name="name", re_code="name")

        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)
        link = FragmentLink.objects.create(fragment=fragment, antiquarian=a)
        self.assertEqual(link.display_order_one_indexed(), link.order + 1)
        self.assertEqual(link.get_display_name(), "name F1")
        link.antiquarian = None
        self.assertEqual(link.get_display_name(), "Anonymous F1")

    def test_display_names_in_error(self):
        link = FragmentLink()
        self.assertIsNone(link.order)
        self.assertIsNone(link.work_order)
        self.assertEqual(link.display_order_one_indexed(), "ERR")
        self.assertEqual(link.display_work_order_one_indexed(), "ERR")

        self.assertIsNone(link.work)
        self.assertEqual(link.get_work_display_name(), "")

    def test_link_antiquarian_reverse_accessor(self):
        # check that the reverse method of making associations doesn't fail
        # though we would probaby not use it
        a = Antiquarian.objects.create(name="name0", re_code="name0")
        for i in range(0, 10):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)

            # NB we would normally create the fragmentlink object
            # itself as we can then set the definite flag which
            # defaults to false if we add them this way
            fragment.linked_antiquarians.add(a)

        self.assertEqual(
            a.fragments.count(), FragmentLink.objects.filter(antiquarian=a).count()
        )
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a)):
            self.assertEqual(count, link.order)

    def test_link_antiquarian_orders_sequentially(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        for i in range(0, 10):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)

            # NB we would normally create the fragmentlink object
            # itself as we can then set the definite flag which
            # defaults to false if we add them this way
            a0.fragments.add(fragment)
            a1.fragments.add(fragment)

            self.assertEqual(FragmentLink.objects.filter(antiquarian=a0).count(), i + 1)
            # also check reverse accessor
            self.assertEqual(a0.fragmentlinks.count(), i + 1)
            self.assertEqual(
                FragmentLink.objects.get(antiquarian=a0, fragment=fragment).order, i
            )

            self.assertEqual(FragmentLink.objects.filter(antiquarian=a1).count(), i + 1)
            # also check reverse accessor
            self.assertEqual(a1.fragmentlinks.count(), i + 1)
            self.assertEqual(
                FragmentLink.objects.get(antiquarian=a1, fragment=fragment).order, i
            )

        self.assertEqual(
            a0.fragments.count(), FragmentLink.objects.filter(antiquarian=a0).count()
        )
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a0)):
            self.assertEqual(count, link.order)

        self.assertEqual(
            a1.fragments.count(), FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a1)):
            self.assertEqual(count, link.order)

    def test_removing_fragments_reorders_links(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        for i in range(0, 10):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)
            a0.fragments.add(fragment)
            a1.fragments.add(fragment)

        # remove some links and check the indexes are reshuffled
        to_remove = [a0.fragments.all()[i] for i in (1, 3, 5, 7)]
        for f in to_remove:
            a0.fragments.remove(f)
            link_qs = FragmentLink.objects.filter(antiquarian=a0)
            self.assertEqual(link_qs.count(), a0.fragments.count())
            for count, link in enumerate(link_qs):
                self.assertEqual(count, link.order)

        # other antiquarian unaffected
        self.assertEqual(
            a1.fragments.count(), FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a1)):
            self.assertEqual(count, link.order)

    def test_deleting_fragments_reorders_links(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        for i in range(0, 10):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)
            a0.fragments.add(fragment)
            a1.fragments.add(fragment)

        # delete some fragments and check the indexes are reshuffled
        to_delete = [a0.fragments.all()[i] for i in (1, 3, 5, 7)]
        for f in to_delete:
            f.delete()
            link_qs = FragmentLink.objects.filter(antiquarian=a0)
            self.assertEqual(link_qs.count(), a0.fragments.count())
            for count, link in enumerate(link_qs):
                self.assertEqual(count, link.order)

        # other antiquarian unaffected
        self.assertEqual(
            a1.fragments.count(), FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a1)):
            self.assertEqual(count, link.order)

    def test_deleting_orphan_fragments_reorders_links(self):
        COUNT = 10
        for i in range(0, COUNT):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)
            FragmentLink.objects.create(fragment=fragment)

        qs = FragmentLink.objects.filter(antiquarian__isnull=True)
        self.assertEqual(COUNT, qs.count())

        for count, link in enumerate(qs):
            self.assertEqual(count, link.order)

        # remove one out of the middle
        link = qs.all()[5]
        link.delete()

        qs = FragmentLink.objects.filter(antiquarian__isnull=True)
        self.assertEqual(COUNT - 1, qs.count())

        for count, link in enumerate(qs):
            self.assertEqual(count, link.order)

        # special cases, test removing first one
        link = qs.first()
        link.delete()

        qs = FragmentLink.objects.filter(antiquarian__isnull=True)
        self.assertEqual(COUNT - 2, qs.count())

        for count, link in enumerate(qs):
            self.assertEqual(count, link.order)

    def test_deleting_antiquarian_removes_link(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        for i in range(0, 10):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)
            a0.fragments.add(fragment)
            a1.fragments.add(fragment)

        # delete one antiquarian and all these links should go
        a0.delete()
        self.assertEqual(0, FragmentLink.objects.filter(antiquarian=a0).count())

        # other antiquarian unaffected
        self.assertEqual(
            a1.fragments.count(), FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a1)):
            self.assertEqual(count, link.order)


# removing links from one A leaves links for another alone
# deleting antiquarians removes the links and makes work links anon
# removing works should remove all links to them as they do not
# turn into antiquarian links


class TestWorkLinkScheme(TestCase):
    NUM = 10

    REMOVE_SINGLE = 1
    REMOVE_MULTI = 2
    REMOVE_CLEAR = 3
    REMOVE_SET_BLANK = 4

    def setUp(self):
        # add an antiquarian with a work
        self.antiquarian = Antiquarian.objects.create(name="name", re_code="name")
        self.work = Work.objects.create(name="work")
        self.antiquarian.works.add(self.work)

        for i in range(0, self.NUM):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)
            testimonium = Testimonium.objects.create(**data)

            # add links to antiquarian directly
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=fragment,
                definite_antiquarian=True,
            )
            # Only create work links for half the testimonia
            unknown_work = self.antiquarian.unknown_work
            work = self.work if i % 2 == 0 else unknown_work
            TestimoniumLink.objects.create(
                antiquarian=self.antiquarian,
                work=work,
                testimonium=testimonium,
                definite_antiquarian=True,
            )
            # add links to works
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=fragment,
                work=self.work,
                definite_antiquarian=True,
            )

    def test_link_antiquarian_orders_sequentially(self):
        # we should have two lots of links here as links should have been
        # automatically created via the work
        self.assertEqual(self.antiquarian.fragments.count(), 2 * self.NUM)
        # but they should all be ordered sequentially
        for count, link in enumerate(
            FragmentLink.objects.filter(antiquarian=self.antiquarian)
        ):
            self.assertEqual(count, link.order)

    def test_testimonia_without_work_ordered_first(self):
        """TestimoniaLinks with no work specified should be ordered before
        those with a linked work"""
        self.antiquarian.reindex_fragment_and_testimonium_links()
        # Odd numbered testimonia were not linked to works so we expect them to be first
        names_order = [f"name{i}" for i in [1, 3, 5, 7, 9, 0, 2, 4, 6, 8]]
        for count, name in enumerate(names_order):
            testimonium = Testimonium.objects.get(name=name)
            self.assertEqual(
                TestimoniumLink.objects.filter(testimonium=testimonium).last().order,
                count,
            )

    def test_ordered_fragments_method(self):
        ordered_fragments = [f.pk for f in self.antiquarian.ordered_fragments()]
        ground_truth = sorted(
            list(
                set(
                    [
                        link.fragment.pk
                        for link in FragmentLink.objects.filter(
                            antiquarian=self.antiquarian
                        )
                    ]
                )
            )
        )
        self.assertEqual(ordered_fragments, ground_truth)

    def test_remove_work_moves_links(self):
        # removing the antiquarian as work author should move links to unknown work
        self.antiquarian.works.remove(self.work)

        # we should now have only links directly to the antiquarian - i.e unknown work
        self.assertEqual(self.antiquarian.fragmentlinks.count(), self.NUM)
        for link in self.antiquarian.fragmentlinks.all():
            self.assertTrue(link.work.unknown)

        # the antiquarian links have been reordered
        for count, link in enumerate(
            FragmentLink.objects.filter(antiquarian=self.antiquarian)
        ):
            self.assertEqual(count, link.order)

        # there are no links to the antiquarian via the work
        self.assertFalse(
            FragmentLink.objects.filter(
                antiquarian=self.antiquarian, work=self.work
            ).exists()
        )

        # the fragment links to the work are still there
        self.assertEqual(
            FragmentLink.objects.filter(
                antiquarian__isnull=True, work=self.work
            ).count(),
            self.NUM,
        )
        # and have been reordered
        for count, link in enumerate(
            FragmentLink.objects.filter(antiquarian__isnull=True, work=self.work)
        ):
            self.assertEqual(count, link.order)

    def test_add_work_to_antiquarian_inherits_links(self):
        # if we add a second antiquarian to a work, then they
        # should inherit all the links already given to that work
        a = Antiquarian.objects.create(name="new")
        a.works.add(self.work)

        self.assertEqual(a.fragments.count(), self.NUM)

        # check the links are created
        for link in a.fragmentlinks.all():
            self.assertEqual(link.work, self.work)

        # and they are in order wrt this antiquarian
        for count, link in enumerate(FragmentLink.objects.filter(antiquarian=a)):
            self.assertEqual(count, link.order)

        # the other antiquarian should be unaffected by this
        self.assertEqual(self.antiquarian.fragments.count(), 2 * self.NUM)
        # and their links should still be ordered sequentially
        for count, link in enumerate(
            FragmentLink.objects.filter(antiquarian=self.antiquarian)
        ):
            self.assertEqual(count, link.order)

    def test_ordered_works(self):
        a = Antiquarian.objects.create(name="new")
        names = [
            "work one",
            "work two",
            "work three",
        ]
        for name in names:
            a.works.add(Work.objects.create(name=name))

        self.assertEqual(
            [w.name for w in a.ordered_works.all()], names + ["Unknown Work"]
        )
        # try moving a work down in the order
        link = a.worklink_set.first()
        link.down()

        # should have reordered
        self.assertEqual(
            [w.name for w in a.ordered_works.all()],
            [
                "work two",
                "work one",
                "work three",
                "Unknown Work",
            ],
        )

        link = a.worklink_set.exclude(work__unknown=True).last()
        link.up()

        # should have reordered
        self.assertEqual(
            [w.name for w in a.ordered_works.all()],
            [
                "work two",
                "work three",
                "work one",
                "Unknown Work",
            ],
        )

    def test_remove_author_removes_link(self):
        # remove all existing objects
        Antiquarian.objects.all().delete()
        Work.objects.all().delete()
        FragmentLink.objects.all().delete()

        self.assertEqual(Antiquarian.objects.count(), 0)
        self.assertEqual(Work.objects.count(), 0)
        self.assertEqual(FragmentLink.objects.count(), 0)

        w = Work.objects.create(name="work")
        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        # link both the antiquarians to this work
        a0.works.add(w)
        a1.works.add(w)

        # create fragment and links to this work (and through the work)
        # to the antiquarians
        f = Fragment.objects.create()
        FragmentLink.objects.create(antiquarian=a0, work=w, fragment=f)
        FragmentLink.objects.create(antiquarian=a1, work=w, fragment=f)

        self.assertEqual(FragmentLink.objects.count(), 2)

        # now remove one author from the work
        a0.works.remove(w)

        # this should have removed their fragment link and kept the other
        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertEqual(FragmentLink.objects.first().antiquarian, a1)

        # now remove that author
        a1.works.remove(w)

        # this should not have removed their fragment link as it is the last
        # one. We should instead preserve the link to the work and set
        # the antiquarian to None
        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertIsNone(FragmentLink.objects.first().antiquarian)

        # in case we ever add them back
        a0.works.add(w)

        # in which case the null fragment link is updated to
        # reflect this

        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertEqual(FragmentLink.objects.first().antiquarian, a0)

    def test_delete_work_moves_links(self):
        """When a work is removed, the links should assign themselves to the Unknown Work of the Antiquarian"""
        # removing the antiquarian as work author should move
        # linked fragments to Unknown Work
        work_pk = self.work.pk
        self.work.delete()

        # we should now have only links directly to the antiquarian - put in Unknown Work
        self.assertEqual(self.antiquarian.fragments.count(), self.NUM)
        for link in self.antiquarian.fragmentlinks.all():
            self.assertEqual(link.work, link.antiquarian.unknown_work)

        # fragment links via work should be deleted
        self.assertEqual(
            FragmentLink.objects.filter(antiquarian=self.antiquarian).count(), self.NUM
        )

        # the antiquarian links have been reordered
        for count, link in enumerate(
            FragmentLink.objects.filter(antiquarian=self.antiquarian)
        ):
            self.assertEqual(count, link.order)

        # there are no links to the antiquarian via the work
        self.assertEqual(
            0,
            FragmentLink.objects.filter(
                antiquarian=self.antiquarian, work__pk=work_pk
            ).count(),
        )

        # the fragment links to the work are gone
        self.assertEqual(FragmentLink.objects.filter(work__pk=work_pk).count(), 0)

        # there should be no stray links lying around
        self.assertEqual(FragmentLink.objects.all().count(), self.NUM)

    def test_add_work_via_reverse_accessor_generates_links(self):
        # can connect works to antiquarians using
        # antiquarian.works.add(work)
        # and also
        # work.antiquarian_set.add(antiquarian)
        # and both of these methods should create
        # any relevant fragment links
        work = Work.objects.create(name="another")
        for fragment in Fragment.objects.all():
            FragmentLink.objects.create(
                fragment=fragment,
                work=work,
                definite_work=True,
                definite_antiquarian=True,
            )
        antiquarian = Antiquarian.objects.create(name="hi", re_code=12345)
        self.assertEqual(antiquarian.fragmentlinks.count(), 0)
        work.antiquarian_set.add(antiquarian)
        self.assertEqual(antiquarian.fragmentlinks.count(), Fragment.objects.count())

    def test_add_delete_single_work_updates_links(self):
        """After adding a work to an Antiquarian, its links should then be associated with that Antiquarian.
        Even when the work is deleted, those links should point to Unknown Work for that Antiquarian
        """
        self._run_test_add_del_multi_works_updates_links(self.REMOVE_SINGLE)

    def test_add_delete_multi_work_updates_links(self):
        self._run_test_add_del_multi_works_updates_links(self.REMOVE_MULTI)

    def test_add_clear_works_updates_links(self):
        self._run_test_add_del_multi_works_updates_links(
            self.REMOVE_CLEAR,
        )

    def test_add_set_blank_works_updates_links(self):
        self._run_test_add_del_multi_works_updates_links(self.REMOVE_SET_BLANK)

    def _run_test_add_del_multi_works_updates_links(self, method):
        # removing the antiquarian as work author should deassociated all
        # linked fragments when multiple works removed at once
        starting_fragmentlinks_count = self.antiquarian.fragmentlinks.all().count()

        ADD = 4
        # with transaction.atomic():
        for i in range(0, ADD):
            # create a work
            work = Work.objects.create(name="another")
            # link all the fragments to it
            for fragment in Fragment.objects.all():
                FragmentLink.objects.create(
                    antiquarian=self.antiquarian,
                    fragment=fragment,
                    work=work,
                    definite_work=True,
                )

        works = Work.objects.all()

        # set up creates a work called 'work', we've created
        # four others here called 'another' and there is a default Unknown Work
        self.assertEqual(ADD + 2, works.count())

        # set the antiquarian works all at once
        self.antiquarian.works.set(works)

        ant_works = self.antiquarian.works.all()
        ant_fragmentlinks = self.antiquarian.fragmentlinks.all()

        # check it worked - we should have 5 works in total
        self.assertEqual(works.count(), ant_works.count())

        # we should at this point have 5 sets
        # 4 linked via the work 'another' and one other work = 5
        expected = (self.NUM * ADD) + starting_fragmentlinks_count
        self.assertEqual(ant_fragmentlinks.count(), expected)

        if method == self.REMOVE_SINGLE:
            self.antiquarian.works.remove(works.first())  # one only
        elif method == self.REMOVE_MULTI:
            self.antiquarian.works.remove(*works.all()[:2])  # subset
        elif method == self.REMOVE_CLEAR:
            self.antiquarian.works.clear()  # has different signal behaviour
        elif method == self.REMOVE_SET_BLANK:
            self.antiquarian.works.set(Work.objects.none())  # set to empty

        # antiquarian should now have fewer links directly to it
        expected = (ant_works.count()) * self.NUM
        self.assertEqual(ant_fragmentlinks.count(), expected)
        # the antiquarian links have been reordered
        for count, link in enumerate(
            FragmentLink.objects.filter(antiquarian=self.antiquarian)
        ):
            self.assertEqual(count, link.order)

        # the fragment links to the works should still be there
        nfragments = Fragment.objects.count()
        nworks = Work.objects.count()

        # there should be no stray links lying around
        self.assertEqual(FragmentLink.objects.all().count(), nfragments * nworks)

        for work in Work.objects.all():
            self.assertEqual(FragmentLink.objects.filter(work=work).count(), nfragments)

        # check that orphaned works have been reordered
        # (with respect to blank antiquarian)
        for count, link in enumerate(
            FragmentLink.objects.filter(antiquarian__isnull=True)
        ):
            self.assertEqual(count, link.order)


class TestLinkScheme(TestCase):
    def setUp(self):
        """The new way of defining definite/possible aspects is broken down for antiquarians, works and books.
        This means each link will be definite or not for each and will not be null.
        """
        # add an antiquarian with a work
        self.antiquarian = Antiquarian.objects.create(name="name", re_code="name")
        self.work = Work.objects.create(name="work")
        self.antiquarian.works.add(self.work)
        self.book = Book.objects.create(work=self.work, number=1)

        data = {
            "name": "name",
        }
        self.fragment = Fragment.objects.create(**data)
        self.testimonium = Testimonium.objects.create(**data)
        self.anonymous_fragment = AnonymousFragment.objects.create(**data)

    def test_add_work_fragment_updates_antiquarian(self):
        FragmentLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            fragment=self.fragment,
        )
        self.assertEqual(self.antiquarian.fragments.count(), 1)

    def test_remove_work_fragment_updates_antiquariam(self):
        link = FragmentLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            fragment=self.fragment,
        )
        link.delete()
        self.assertEqual(self.antiquarian.fragments.count(), 0)

    def test_fragment_queryset_methods(self):
        self.assertEqual(0, len(self.fragment.definite_work_links()))
        self.assertEqual(0, len(self.fragment.possible_work_links()))
        self.assertEqual(0, len(self.fragment.definite_book_links()))
        self.assertEqual(0, len(self.fragment.possible_book_links()))
        self.assertEqual(0, self.fragment.definite_antiquarian_links().count())
        self.assertEqual(0, self.fragment.possible_antiquarian_links().count())

        link = FragmentLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            fragment=self.fragment,
            definite_work=True,
        )

        self.assertEqual(0, len(self.fragment.definite_book_links()))
        self.assertEqual(1, len(self.fragment.possible_book_links()))
        self.assertEqual(1, len(self.fragment.definite_work_links()))
        self.assertEqual(0, len(self.fragment.possible_work_links()))
        self.assertEqual(0, self.fragment.definite_antiquarian_links().count())
        self.assertEqual(1, self.fragment.possible_antiquarian_links().count())

        link.definite_work = False
        link.save()

        self.assertEqual(0, len(self.fragment.definite_book_links()))
        self.assertEqual(1, len(self.fragment.possible_book_links()))
        self.assertEqual(0, len(self.fragment.definite_work_links()))
        self.assertEqual(1, len(self.fragment.possible_work_links()))
        self.assertEqual(0, self.fragment.definite_antiquarian_links().count())
        self.assertEqual(1, self.fragment.possible_antiquarian_links().count())

        link.book = self.book
        link.save()
        self.assertEqual(0, len(self.fragment.definite_book_links()))
        self.assertEqual(1, len(self.fragment.possible_book_links()))
        self.assertEqual(0, len(self.fragment.definite_work_links()))
        self.assertEqual(1, len(self.fragment.possible_work_links()))
        self.assertEqual(0, self.fragment.definite_antiquarian_links().count())
        self.assertEqual(1, self.fragment.possible_antiquarian_links().count())

        link.work = None
        link.definite_antiquarian = True
        link.save()

        self.assertEqual(0, len(self.fragment.definite_book_links()))
        self.assertEqual(1, len(self.fragment.possible_book_links()))
        self.assertEqual(0, len(self.fragment.definite_work_links()))
        self.assertEqual(1, len(self.fragment.possible_work_links()))
        self.assertEqual(1, self.fragment.definite_antiquarian_links().count())
        self.assertEqual(0, self.fragment.possible_antiquarian_links().count())

        link.definite_antiquarian = False
        link.save()

        self.assertEqual(0, len(self.fragment.definite_book_links()))
        self.assertEqual(1, len(self.fragment.possible_book_links()))
        self.assertEqual(0, len(self.fragment.definite_work_links()))
        self.assertEqual(1, len(self.fragment.possible_work_links()))
        self.assertEqual(0, self.fragment.definite_antiquarian_links().count())
        self.assertEqual(1, self.fragment.possible_antiquarian_links().count())

    def test_testimonium_queryset_methods(self):
        self.assertEqual(0, len(self.testimonium.definite_book_links()))
        self.assertEqual(0, len(self.testimonium.possible_book_links()))
        self.assertEqual(0, len(self.testimonium.definite_work_links()))
        self.assertEqual(0, len(self.testimonium.possible_work_links()))
        self.assertEqual(0, self.testimonium.definite_antiquarian_links().count())
        self.assertEqual(0, self.testimonium.possible_antiquarian_links().count())

        link = TestimoniumLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            testimonium=self.testimonium,
            definite_work=True,
        )

        self.assertEqual(0, len(self.testimonium.definite_book_links()))
        self.assertEqual(1, len(self.testimonium.possible_book_links()))
        self.assertEqual(1, len(self.testimonium.definite_work_links()))
        self.assertEqual(0, len(self.testimonium.possible_work_links()))
        self.assertEqual(0, self.testimonium.definite_antiquarian_links().count())
        self.assertEqual(1, self.testimonium.possible_antiquarian_links().count())

        link.definite_work = False
        link.save()

        self.assertEqual(0, len(self.testimonium.definite_book_links()))
        self.assertEqual(1, len(self.testimonium.possible_book_links()))
        self.assertEqual(0, len(self.testimonium.definite_work_links()))
        self.assertEqual(1, len(self.testimonium.possible_work_links()))
        self.assertEqual(0, self.testimonium.definite_antiquarian_links().count())
        self.assertEqual(1, self.testimonium.possible_antiquarian_links().count())

        link.book = self.book
        link.save()
        self.assertEqual(0, len(self.testimonium.definite_book_links()))
        self.assertEqual(1, len(self.testimonium.possible_book_links()))
        self.assertEqual(0, len(self.testimonium.definite_work_links()))
        self.assertEqual(1, len(self.testimonium.possible_work_links()))
        self.assertEqual(0, self.testimonium.definite_antiquarian_links().count())
        self.assertEqual(1, self.testimonium.possible_antiquarian_links().count())

        link.work = None
        link.definite_antiquarian = True
        link.save()

        self.assertEqual(0, len(self.testimonium.definite_book_links()))
        self.assertEqual(1, len(self.testimonium.possible_book_links()))
        self.assertEqual(0, len(self.testimonium.definite_work_links()))
        self.assertEqual(1, len(self.testimonium.possible_work_links()))
        self.assertEqual(1, self.testimonium.definite_antiquarian_links().count())
        self.assertEqual(0, self.testimonium.possible_antiquarian_links().count())

        link.definite_antiquarian = False
        link.save()

        self.assertEqual(0, len(self.testimonium.definite_book_links()))
        self.assertEqual(1, len(self.testimonium.possible_book_links()))
        self.assertEqual(0, len(self.testimonium.definite_work_links()))
        self.assertEqual(1, len(self.testimonium.possible_work_links()))
        self.assertEqual(0, self.testimonium.definite_antiquarian_links().count())
        self.assertEqual(1, self.testimonium.possible_antiquarian_links().count())

    def test_add_antiquarian_fragment_ignores_work(self):
        FragmentLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            fragment=self.fragment,
            definite_antiquarian=True,
            definite_work=True,
        )
        self.assertEqual(len(self.fragment.definite_work_links()), 1)
        # add more links to the antiquarian and the work should be unaffected
        for i in range(0, 10):
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=self.fragment,
                definite_antiquarian=True,
            )
        self.assertEqual(len(self.fragment.definite_work_links()), 1)

    def test_get_all_names(self):
        # all names that this fragment is known by according to the
        # links it has with various objects
        a = Antiquarian.objects.create(name="name1", re_code="name1")
        data = {
            "name": "name1",
        }
        fragment = Fragment.objects.create(**data)
        linkfa1 = FragmentLink.objects.create(fragment=fragment, antiquarian=a)
        linkfa2 = FragmentLink.objects.create(fragment=fragment, antiquarian=a)
        # should be ordered wrt antiquarian then order
        self.assertEqual(
            fragment.get_all_names(),
            [
                "{}".format(linkfa1.get_display_name()),
                "{}".format(linkfa2.get_display_name()),
            ],
        )

        testimonium = Testimonium.objects.create(**data)
        linkta1 = TestimoniumLink.objects.create(testimonium=testimonium, antiquarian=a)
        linkta2 = TestimoniumLink.objects.create(testimonium=testimonium, antiquarian=a)
        # should be ordered wrt antiquarian then order
        self.assertEqual(
            testimonium.get_all_names(),
            [
                "{}".format(linkta1.get_display_name()),
                "{}".format(linkta2.get_display_name()),
            ],
        )


class TestWorkLinkUpdateScheme(TestCase):
    def setUp(self):
        # add an antiquarian with a work
        self.antiquarian = Antiquarian.objects.create(name="name", re_code="name")
        self.work = Work.objects.create(name="work")
        self.antiquarian.works.add(self.work)
        self.book = Book.objects.create(work=self.work, number=1)

        data = {
            "name": "name",
        }
        self.fragment = Fragment.objects.create(**data)
        self.testimonium = Testimonium.objects.create(**data)

    def test_add_work_fragment_queryset(self):
        FragmentLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            fragment=self.fragment,
        )
        self.assertEqual(self.work.all_fragments().count(), 1)

    def test_add_work_fragment_sets_work_index(self):
        link_pks = []
        for _ in range(0, 10):
            link = FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                work=self.work,
                fragment=self.fragment,
            )
            link_pks.append(link.pk)

        for count, pk in enumerate(link_pks):
            link = FragmentLink.objects.get(pk=pk)
            self.assertEqual(link.work_order, count)
            self.assertEqual(link.display_work_order_one_indexed(), count + 1)

    def test_work_order_different_to_order(self):
        # not the same thing and can vary independently
        for _ in range(0, 10):
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                work=self.work,
                fragment=self.fragment,
            )
            # now independently set for the antiquarian - these will be in Unknown Work
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=self.fragment,
            )

        # work_order should be set wrt links with a work link
        qs = FragmentLink.objects.filter(antiquarian=self.antiquarian)

        for count, link in enumerate(
            qs.filter(work__unknown=False).order_by("work_order")
        ):
            self.assertEqual(link.work_order, count)
            self.assertEqual(link.display_work_order_one_indexed(), count + 1)

        # the links to antiquarians should be independent as before
        for count, link in enumerate(qs.order_by("order")):
            self.assertEqual(link.order, count)
            self.assertEqual(link.display_order_one_indexed(), count + 1)

    def test_remove_work_fragment_reindexes_work_index(self):
        link_pks = []
        for _ in range(0, 10):
            link = FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                work=self.work,
                fragment=self.fragment,
            )
            link_pks.append(link.pk)

        # delete some of them
        FragmentLink.objects.filter(pk__in=(8, 6, 3)).delete()

        # indexes should have been patched
        for count, pk in enumerate(link_pks):
            link = FragmentLink.objects.get(pk=pk)
            self.assertEqual(link.work_order, count)

    def test_add_work_testimonium_queryset(self):
        TestimoniumLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            testimonium=self.testimonium,
        )
        self.assertEqual(self.work.all_testimonia().count(), 1)

    def test_add_work_testimonium_sets_work_index(self):
        link_pks = []
        # from django.db import transaction
        for _ in range(0, 10):
            # with transaction.atomic():
            link = TestimoniumLink.objects.create(
                antiquarian=self.antiquarian,
                work=self.work,
                testimonium=self.testimonium,
            )
            link_pks.append(link.pk)

        for count, pk in enumerate(link_pks):
            link = TestimoniumLink.objects.get(pk=pk)
            self.assertEqual(link.work_order, count)
            self.assertEqual(link.display_work_order_one_indexed(), count + 1)

    def test_remove_work_testimonium_reindexes_work_index(self):
        link_pks = []
        for _ in range(0, 10):
            link = TestimoniumLink.objects.create(
                antiquarian=self.antiquarian,
                work=self.work,
                testimonium=self.testimonium,
            )
            link_pks.append(link.pk)

        # delete some of them
        to_delete = [3, 6, 8]
        for count, pk in enumerate(link_pks):
            if count in to_delete:
                TestimoniumLink.objects.get(pk=pk).delete()
                link_pks.remove(pk)

        # indexes should have been patched
        for count, pk in enumerate(link_pks):
            link = TestimoniumLink.objects.get(pk=pk)
            self.assertEqual(link.work_order, count)


class TestFragmentWorkOrderingScheme(TestCase):
    NUM = 5

    def setUp(self):
        # add an antiquarian with a work
        self.antiquarian = Antiquarian.objects.create(name="name", re_code="name")
        self.work = Work.objects.create(name="work")
        self.antiquarian.works.add(self.work)

        for i in range(0, self.NUM):
            data = {
                "name": "name{}".format(i),
            }
            fragment = Fragment.objects.create(**data)

            # add links to antiquarian directly
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=fragment,
                work=self.work,
                definite_antiquarian=True,
                order_in_book=i,
            )

    def _get_fragment_names(self):
        return [
            link.fragment.name
            for link in self.work.antiquarian_work_fragmentlinks.order_by(
                "work_order", "order_in_book"
            )
        ]

    def test_up_by_book(self):
        fragment_names = self._get_fragment_names()
        self.assertEqual(len(fragment_names), 5)
        test_link = self.work.antiquarian_work_fragmentlinks.last()

        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (0, 1, 2, 3, 4)]
        )

        test_link.up_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (0, 1, 2, 4, 3)]
        )

        test_link.up_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (0, 1, 4, 2, 3)]
        )

        test_link.up_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (0, 4, 1, 2, 3)]
        )

        test_link.up_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (4, 0, 1, 2, 3)]
        )

        # attempt to move above pos 0 has no effect and does not barf
        test_link.up_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (4, 0, 1, 2, 3)]
        )

    def test_down_by_book(self):
        fragment_names = self._get_fragment_names()
        self.assertEqual(len(fragment_names), 5)
        test_link = self.work.antiquarian_work_fragmentlinks.first()

        test_link.down_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (1, 0, 2, 3, 4)]
        )

        test_link.down_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (1, 2, 0, 3, 4)]
        )

        test_link.down_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (1, 2, 3, 0, 4)]
        )

        test_link.down_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (1, 2, 3, 4, 0)]
        )

        # attempt to move off the end has no effect and does not barf
        test_link.down_by_book()
        self.assertEqual(
            self._get_fragment_names(), [fragment_names[i] for i in (1, 2, 3, 4, 0)]
        )


class TestReindexCollection(TestCase):
    # as the nature of the values is tbd, this test will only check
    # that the collection id is actually set to some non
    # blank/null value on all fragments etc.
    def test_reindex_sets_collection_id(self):
        # create some objects
        for i in range(0, 10):
            Fragment.objects.create()
            Testimonium.objects.create()
            AnonymousFragment.objects.create()

        for f in Fragment.objects.all():
            self.assertIsNone(f.collection_id)

        for t in Testimonium.objects.all():
            self.assertIsNone(t.collection_id)

        for a in AnonymousFragment.objects.all():
            self.assertIsNone(a.collection_id)

        from rard.research.models.base import HistoricalBaseModel

        HistoricalBaseModel.reindex_collection()

        for f in Fragment.objects.all():
            self.assertIsNotNone(f.collection_id)

        for t in Testimonium.objects.all():
            self.assertIsNotNone(t.collection_id)

        for a in AnonymousFragment.objects.all():
            self.assertIsNotNone(a.collection_id)


class TestAppositaLinkScheme(TestCase):
    def test_add_apposita_creates_apposita_links(self):
        # given a fragmentlink we need to ensure apposita links
        # are created when added to the fragment owning the link
        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)

        NLINKS = 5
        for i in range(0, 5):
            a = Antiquarian.objects.create(name="name", re_code=i)
            FragmentLink.objects.create(fragment=fragment, antiquarian=a)

        # add apposita to the fragment
        NUM = 10
        for i in range(0, NUM):
            anon = AnonymousFragment.objects.create()
            fragment.apposita.add(anon)

        # we should now have a appositum fragment link in each of these
        # apposita (auto-created)
        for anon in fragment.apposita.all():
            self.assertEqual(anon.appositumfragmentlinks_from.count(), NLINKS)

    def test_add_fragment_link_adds_apposita_links(self):
        # this time we already have apposita linked to the fragment
        # and we test whether adding a fragmentlink to this
        # fragment creates apposita links also
        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)

        # add apposita to the fragment
        NUM = 10
        for i in range(0, NUM):
            anon = AnonymousFragment.objects.create()
            fragment.apposita.add(anon)

        NLINKS = 5
        for i in range(0, 5):
            a = Antiquarian.objects.create(name="name", re_code=i)
            FragmentLink.objects.create(fragment=fragment, antiquarian=a)

        # we should now have a appositum fragment link in each of these
        # apposita (auto-created)
        for anon in fragment.apposita.all():
            self.assertEqual(anon.appositumfragmentlinks_from.count(), NLINKS)

    def test_remove_apposita_removes_apposita_links(self):
        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)

        # add apposita to the fragment
        NUM = 10
        for i in range(0, NUM):
            anon = AnonymousFragment.objects.create()
            fragment.apposita.add(anon)

        NLINKS = 5
        for i in range(0, 5):
            a = Antiquarian.objects.create(name="name", re_code=i)
            FragmentLink.objects.create(fragment=fragment, antiquarian=a)

        # now we have apposita links for all fragmentlinks. Remove apposita
        # and check we remove the links
        for anon in fragment.apposita.all():
            self.assertEqual(anon.appositumfragmentlinks_from.count(), NLINKS)
            fragment.apposita.remove(anon)
            self.assertEqual(anon.appositumfragmentlinks_from.count(), 0)

        self.assertEqual(AppositumFragmentLink.objects.count(), 0)

    def test_remove_fragment_link_removes_apposita_links(self):
        data = {
            "name": "name",
        }
        fragment = Fragment.objects.create(**data)

        # add apposita to the fragment
        NUM = 10
        for i in range(0, NUM):
            anon = AnonymousFragment.objects.create()
            fragment.apposita.add(anon)

        NLINKS = 5
        for i in range(0, 5):
            a = Antiquarian.objects.create(name="name", re_code=i)
            link = FragmentLink.objects.create(fragment=fragment, antiquarian=a)

        # now we have apposita links for all fragmentlinks. Remove fragment
        # links and check we remove the apposita links
        for count, link in enumerate(fragment.antiquarian_fragmentlinks.all()):
            link.delete()
            for anon in fragment.apposita.all():
                self.assertEqual(
                    anon.appositumfragmentlinks_from.count(), NLINKS - count - 1
                )
        self.assertEqual(AppositumFragmentLink.objects.count(), 0)

    def test_remove_author_removes_appositum_links(self):
        # remove all existing objects
        Antiquarian.objects.all().delete()
        Work.objects.all().delete()
        FragmentLink.objects.all().delete()

        self.assertEqual(Antiquarian.objects.count(), 0)
        self.assertEqual(Work.objects.count(), 0)
        self.assertEqual(FragmentLink.objects.count(), 0)

        w = Work.objects.create(name="work")
        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        # link both the antiquarians to this work
        a0.works.add(w)
        a1.works.add(w)

        # create fragment and links to this work (and through the work)
        # to the antiquarians
        f = Fragment.objects.create()
        anon = AnonymousFragment.objects.create()
        f.apposita.add(anon)

        FragmentLink.objects.create(antiquarian=a0, work=w, fragment=f)
        FragmentLink.objects.create(antiquarian=a1, work=w, fragment=f)

        self.assertEqual(FragmentLink.objects.count(), 2)
        self.assertEqual(AppositumFragmentLink.objects.count(), 2)

        # now remove one author from the work
        a0.works.remove(w)

        # this should have removed their fragment link and kept the other
        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertEqual(FragmentLink.objects.first().antiquarian, a1)
        self.assertEqual(AppositumFragmentLink.objects.count(), 1)
        self.assertEqual(AppositumFragmentLink.objects.first().antiquarian, a1)

        # now remove that author
        a1.works.remove(w)

        # this should not have removed their fragment link as it is the last
        # one. We should instead preserve the link to the work and set
        # the antiquarian to None
        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertIsNone(FragmentLink.objects.first().antiquarian)
        self.assertEqual(AppositumFragmentLink.objects.count(), 1)
        self.assertIsNone(AppositumFragmentLink.objects.first().antiquarian)

        # in case we ever add them back
        a0.works.add(w)

        # in which case the null fragment link is updated to
        # reflect this
        self.assertEqual(FragmentLink.objects.count(), 1)
        self.assertEqual(FragmentLink.objects.first().antiquarian, a0)
        self.assertEqual(AppositumFragmentLink.objects.count(), 1)
        self.assertEqual(AppositumFragmentLink.objects.first().antiquarian, a0)

    def test_default_is_non_exclusive(self):
        Antiquarian.objects.all().delete()
        Work.objects.all().delete()
        FragmentLink.objects.all().delete()

        self.assertEqual(Antiquarian.objects.count(), 0)
        self.assertEqual(Work.objects.count(), 0)
        self.assertEqual(FragmentLink.objects.count(), 0)

        w = Work.objects.create(name="work")
        a = Antiquarian.objects.create(name="name0", re_code="name0")

        # link one antiquarian to this work
        a.works.add(w)

        anon = AnonymousFragment.objects.create()
        link = AppositumFragmentLink.objects.create(
            anonymous_fragment=anon, antiquarian=a, work=w
        )

        # we didn't set exclusivity so it should default to false
        self.assertFalse(link.exclusive)

    def test_non_exclusive_appositum_link(self):
        Antiquarian.objects.all().delete()
        Work.objects.all().delete()
        FragmentLink.objects.all().delete()

        self.assertEqual(Antiquarian.objects.count(), 0)
        self.assertEqual(Work.objects.count(), 0)
        self.assertEqual(FragmentLink.objects.count(), 0)

        w = Work.objects.create(name="work")
        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        # link one antiquarian to this work
        a0.works.add(w)

        anon = AnonymousFragment.objects.create()
        AppositumFragmentLink.objects.create(
            anonymous_fragment=anon, antiquarian=a0, work=w, exclusive=False
        )

        self.assertEqual(AppositumFragmentLink.objects.count(), 1)

        # now add the other antiquarian
        a1.works.add(w)

        # non-exclusive links should be auto-created
        self.assertEqual(AppositumFragmentLink.objects.count(), 2)

    def test_exclusive_appositum_link_not_auto_created(self):
        Antiquarian.objects.all().delete()
        Work.objects.all().delete()
        FragmentLink.objects.all().delete()

        self.assertEqual(Antiquarian.objects.count(), 0)
        self.assertEqual(Work.objects.count(), 0)
        self.assertEqual(FragmentLink.objects.count(), 0)

        w = Work.objects.create(name="work")
        a0 = Antiquarian.objects.create(name="name0", re_code="name0")
        a1 = Antiquarian.objects.create(name="name1", re_code="name1")

        # link one antiquarian to this work
        a0.works.add(w)

        anon = AnonymousFragment.objects.create()
        AppositumFragmentLink.objects.create(
            anonymous_fragment=anon, antiquarian=a0, work=w, exclusive=True
        )

        self.assertEqual(AppositumFragmentLink.objects.count(), 1)

        # now add the other antiquarian
        a1.works.add(w)

        # exclusive links should not be auto-created for new antiquarians
        # as they are only
        self.assertEqual(AppositumFragmentLink.objects.count(), 1)
        self.assertEqual(AppositumFragmentLink.objects.first().antiquarian, a0)

    def test_non_exclusive_appositum_link_not_deleted(self):
        # where a link is non-exclusive to a work/antiquarian these
        # links should be preserved to the work like they are for
        # general fragment and testimonium links
        Antiquarian.objects.all().delete()
        Work.objects.all().delete()
        FragmentLink.objects.all().delete()

        self.assertEqual(Antiquarian.objects.count(), 0)
        self.assertEqual(Work.objects.count(), 0)
        self.assertEqual(FragmentLink.objects.count(), 0)

        w = Work.objects.create(name="work")
        a = Antiquarian.objects.create(name="name0", re_code="name0")

        # link one antiquarian to this work
        a.works.add(w)

        anon = AnonymousFragment.objects.create()
        AppositumFragmentLink.objects.create(
            anonymous_fragment=anon, antiquarian=a, work=w, exclusive=False
        )

        self.assertEqual(AppositumFragmentLink.objects.count(), 1)

        # now add the other antiquarian
        a.works.remove(w)

        # exclusive links should not be auto-created for new antiquarians
        # as they are only
        self.assertEqual(AppositumFragmentLink.objects.count(), 1)
        self.assertIsNone(AppositumFragmentLink.objects.first().antiquarian)

    def test_exclusive_appositum_link_deleted(self):
        # where a link is exclusive to a work/antiquarian these
        # should be deleted where an antiquarian has been removed from a work
        # as apposed to the general case where they are set to null
        Antiquarian.objects.all().delete()
        Work.objects.all().delete()
        FragmentLink.objects.all().delete()

        self.assertEqual(Antiquarian.objects.count(), 0)
        self.assertEqual(Work.objects.count(), 0)
        self.assertEqual(FragmentLink.objects.count(), 0)
        self.assertEqual(AppositumFragmentLink.objects.count(), 0)

        w = Work.objects.create(name="work")
        a = Antiquarian.objects.create(name="name0", re_code="name0")

        # link one antiquarian to this work
        a.works.add(w)

        anon = AnonymousFragment.objects.create()
        AppositumFragmentLink.objects.create(
            anonymous_fragment=anon, antiquarian=a, work=w, exclusive=True
        )

        self.assertEqual(AppositumFragmentLink.objects.count(), 1)

        # now add the other antiquarian
        a.works.remove(w)

        # exclusive links should be deleted when this happens
        self.assertEqual(AppositumFragmentLink.objects.count(), 0)

    def test_deleting_linked_book_falls_back_to_unknown_book(self):
        # Remove a book-fragment link and get a work-fragment link
        a = Antiquarian.objects.create(name="aq1", re_code="aq1")
        w = Work.objects.create(name="w1")
        a.works.add(w)
        b = Book.objects.create(work=w, number=1)
        f = Fragment.objects.create()
        FragmentLink.objects.create(fragment=f, work=w, book=b)
        b.delete()
        fls = list(FragmentLink.objects.filter(fragment=f, work=w))
        self.assertEqual(len(fls), 1)
        self.assertEqual(fls[0].book, w.unknown_book)
