import pytest
from django.test import TestCase

from rard.research.models import Antiquarian, Book, Fragment, Testimonium, Work
from rard.research.models.base import FragmentLink, TestimoniumLink

pytestmark = pytest.mark.django_db


class TestAntiquarianLinkScheme(TestCase):

    def test_querysets(self):
        # tinkering with ordering of querysets can cause sideeffects
        # with duplicate entries etcs
        # in the results so we do a sanity check here
        NUM = 20
        stub = 'name{}'
        for model_class in (Fragment, Testimonium):
            for i in range(0, NUM):
                data = {
                    'name': stub.format(i),
                }
                model_class.objects.create(**data)

            self.assertEqual(model_class.objects.count(), NUM)
            for i, obj in enumerate(model_class.objects.all()):
                self.assertEqual(obj.name, stub.format(i))

    def test_linked_property(self):
        a = Antiquarian.objects.create(name='name', re_code='name')
        data = {
            'name': 'name',
        }
        fragment = Fragment.objects.create(**data)
        link = FragmentLink.objects.create(fragment=fragment, antiquarian=a)
        self.assertEqual(link.linked, fragment)
        self.assertEqual(
            a.fragments.count(),
            FragmentLink.objects.filter(antiquarian=a).count()
        )
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a)):
            self.assertEqual(count, link.order)

    def test_display_name(self):
        a = Antiquarian.objects.create(name='name', re_code='name')

        data = {
            'name': 'name',
        }
        fragment = Fragment.objects.create(**data)
        link = FragmentLink.objects.create(fragment=fragment, antiquarian=a)
        self.assertEqual(link.display_order_one_indexed(), link.order+1)
        self.assertEqual(link.get_display_name(), 'name F1')
        link.antiquarian = None
        self.assertEqual(link.get_display_name(), 'Anonymous F1')

    def test_link_antiquarian_reverse_accessor(self):
        # check that the reverse method of making associations doesn't fail
        # though we would probaby not use it
        a = Antiquarian.objects.create(name='name0', re_code='name0')
        for i in range(0, 10):
            data = {
                'name': 'name{}'.format(i),
            }
            fragment = Fragment.objects.create(**data)

            # NB we would normally create the fragmentlink object
            # itself as we can then set the definite flag which
            # defaults to false if we add them this way
            fragment.linked_antiquarians.add(a)

        self.assertEqual(
            a.fragments.count(),
            FragmentLink.objects.filter(antiquarian=a).count()
        )
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a)):
            self.assertEqual(count, link.order)

    def test_link_antiquarian_orders_sequentially(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name='name0', re_code='name0')
        a1 = Antiquarian.objects.create(name='name1', re_code='name1')

        for i in range(0, 10):
            data = {
                'name': 'name{}'.format(i),
            }
            fragment = Fragment.objects.create(**data)

            # NB we would normally create the fragmentlink object
            # itself as we can then set the definite flag which
            # defaults to false if we add them this way
            a0.fragments.add(fragment)
            a1.fragments.add(fragment)

            self.assertEqual(
                FragmentLink.objects.filter(antiquarian=a0).count(),
                i+1
            )
            # also check reverse accessor
            self.assertEqual(a0.fragmentlinks.count(), i+1)
            self.assertEqual(
                FragmentLink.objects.get(
                    antiquarian=a0, fragment=fragment
                ).order,
                i
            )

            self.assertEqual(
                FragmentLink.objects.filter(antiquarian=a1).count(),
                i+1
            )
            # also check reverse accessor
            self.assertEqual(a1.fragmentlinks.count(), i+1)
            self.assertEqual(
                FragmentLink.objects.get(
                    antiquarian=a1, fragment=fragment
                ).order,
                i
            )

        self.assertEqual(
            a0.fragments.count(),
            FragmentLink.objects.filter(antiquarian=a0).count()
        )
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a0)):
            self.assertEqual(count, link.order)

        self.assertEqual(
            a1.fragments.count(),
            FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a1)):
            self.assertEqual(count, link.order)

    def test_removing_fragments_reorders_links(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name='name0', re_code='name0')
        a1 = Antiquarian.objects.create(name='name1', re_code='name1')

        for i in range(0, 10):
            data = {
                'name': 'name{}'.format(i),
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
            a1.fragments.count(),
            FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a1)):
            self.assertEqual(count, link.order)

    def test_deleting_fragments_reorders_links(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name='name0', re_code='name0')
        a1 = Antiquarian.objects.create(name='name1', re_code='name1')

        for i in range(0, 10):
            data = {
                'name': 'name{}'.format(i),
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
            a1.fragments.count(),
            FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a1)):
            self.assertEqual(count, link.order)

    def test_deleting_orphan_fragments_reorders_links(self):
        COUNT = 10
        for i in range(0, COUNT):
            data = {
                'name': 'name{}'.format(i),
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
        self.assertEqual(COUNT-1, qs.count())

        for count, link in enumerate(qs):
            self.assertEqual(count, link.order)

        # special cases, test removing first one
        link = qs.first()
        link.delete()

        qs = FragmentLink.objects.filter(antiquarian__isnull=True)
        self.assertEqual(COUNT-2, qs.count())

        for count, link in enumerate(qs):
            self.assertEqual(count, link.order)

    def test_deleting_antiquarian_removes_link(self):
        self.assertEqual(FragmentLink.objects.count(), 0)

        a0 = Antiquarian.objects.create(name='name0', re_code='name0')
        a1 = Antiquarian.objects.create(name='name1', re_code='name1')

        for i in range(0, 10):
            data = {
                'name': 'name{}'.format(i),
            }
            fragment = Fragment.objects.create(**data)
            a0.fragments.add(fragment)
            a1.fragments.add(fragment)

        # delete one antiquarian and all these links should go
        a0.delete()
        self.assertEqual(
            0,
            FragmentLink.objects.filter(antiquarian=a0).count()
        )

        # other antiquarian unaffected
        self.assertEqual(
            a1.fragments.count(),
            FragmentLink.objects.filter(antiquarian=a1).count()
        )
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a1)):
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
        self.antiquarian = Antiquarian.objects.create(
            name='name', re_code='name'
        )
        self.work = Work.objects.create(name='work')
        self.antiquarian.works.add(self.work)

        for i in range(0, self.NUM):
            data = {
                'name': 'name{}'.format(i),
            }
            fragment = Fragment.objects.create(**data)

            # add links to antiquarian directly
            FragmentLink.objects.create(
                antiquarian=self.antiquarian, fragment=fragment,
                definite=True
            )
            # add links to works
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=fragment,
                work=self.work,
                definite=True
            )

    def test_link_antiquarian_orders_sequentially(self):
        # we should have two lots of links here as links should have been
        # automatically created via the work
        self.assertEqual(self.antiquarian.fragments.count(), 2 * self.NUM)
        # but they should all be ordered sequentially
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=self.antiquarian)):
            self.assertEqual(count, link.order)

    def test_ordered_fragments_method(self):
        ordered_fragments = [
            f.pk for f in self.antiquarian.ordered_fragments()
        ]
        ground_truth = sorted(list(set([
            link.fragment.pk for link in
            FragmentLink.objects.filter(antiquarian=self.antiquarian)
        ])))
        self.assertEqual(ordered_fragments, ground_truth)

    def test_remove_work_removes_links(self):
        # removing the antiquarian as work author should deassociated all
        # linked fragments
        self.antiquarian.works.remove(self.work)

        # we should now have only links directly to the antiquarian
        self.assertEqual(self.antiquarian.fragmentlinks.count(), self.NUM)
        for link in self.antiquarian.fragmentlinks.all():
            self.assertIsNone(link.work)

        # the antiquarian links have been reordered
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=self.antiquarian)):
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
            self.NUM
        )
        # and have been reordered
        for count, link in enumerate(
                FragmentLink.objects.filter(
                    antiquarian__isnull=True, work=self.work)):
            self.assertEqual(count, link.order)

    def test_add_work_to_antiquarian_inherits_links(self):
        # if we add a second antiquarian to a work, then they
        # should inherit all the links already given to that work
        a = Antiquarian.objects.create(name='new')
        a.works.add(self.work)

        self.assertEqual(a.fragments.count(), self.NUM)

        # check the links are created
        for link in a.fragmentlinks.all():
            self.assertEqual(link.work, self.work)

        # and they are in order wrt this antiquarian
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=a)):
            self.assertEqual(count, link.order)

        # the other antiquarian should be unaffected by this
        self.assertEqual(self.antiquarian.fragments.count(), 2 * self.NUM)
        # and their links should still be ordered sequentially
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=self.antiquarian)):
            self.assertEqual(count, link.order)

    def test_delete_work_removes_links(self):
        # removing the antiquarian as work author should deassociated all
        # linked fragments
        work_pk = self.work.pk
        self.work.delete()

        # we should now have only links directly to the antiquarian
        self.assertEqual(self.antiquarian.fragments.count(), self.NUM)
        for link in self.antiquarian.fragmentlinks.all():
            self.assertIsNone(link.work)

        # fragment links via work should be deleted
        self.assertEqual(
            FragmentLink.objects.filter(antiquarian=self.antiquarian).count(),
            self.NUM
        )

        # the antiquarian links have been reordered
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=self.antiquarian)):
            self.assertEqual(count, link.order)

        # there are no links to the antiquarian via the work
        self.assertEqual(
            0,
            FragmentLink.objects.filter(
                antiquarian=self.antiquarian, work__pk=work_pk
            ).count()
        )

        # the fragment links to the work are gone
        self.assertEqual(
            FragmentLink.objects.filter(work__pk=work_pk).count(),
            0
        )

        # there should be no stray links lying around
        self.assertEqual(FragmentLink.objects.all().count(), self.NUM)

    def test_add_delete_single_work_updates_links(self):
        self._run_test_add_del_multi_works_updates_links(
            self.REMOVE_SINGLE
        )

    def test_add_delete_multi_work_updates_links(self):
        self._run_test_add_del_multi_works_updates_links(self.REMOVE_MULTI)

    def test_add_clear_works_updates_links(self):
        self._run_test_add_del_multi_works_updates_links(self.REMOVE_CLEAR)

    def test_add_set_blank_works_updates_links(self):
        self._run_test_add_del_multi_works_updates_links(self.REMOVE_SET_BLANK)

    def _run_test_add_del_multi_works_updates_links(self, method):
        # removing the antiquarian as work author should deassociated all
        # linked fragments when multiple works removed at once

        ADD = 4
        # with transaction.atomic():
        for i in range(0, ADD):
            # create a work
            work = Work.objects.create(name='another')
            # link all the fragments to it
            for fragment in Fragment.objects.all():
                FragmentLink.objects.create(
                    antiquarian=self.antiquarian, fragment=fragment, work=work,
                    definite=True
                )
        self.assertEqual(ADD + 1, Work.objects.count())
        # set the antiquarian works all at once
        self.antiquarian.works.set(Work.objects.all())
        # check it worked - we should have 5 works in total
        self.assertEqual(Work.objects.count(), self.antiquarian.works.count())

        # we should at this point have 5 sets
        # linked via the work and one directly = 6
        expected = (Work.objects.count() + 1) * self.NUM
        self.assertEqual(self.antiquarian.fragmentlinks.count(), expected)

        # remove all the works at once (doesn't delete them)
        # for work in self.antiquarian.works.all():
        #     self.antiquarian.works.remove(work)
        # with transaction.atomic():
        if method == self.REMOVE_SINGLE:
            self.antiquarian.works.remove(Work.objects.first())  # one only
        elif method == self.REMOVE_MULTI:
            self.antiquarian.works.remove(*Work.objects.all()[:2])  # subset
        elif method == self.REMOVE_CLEAR:
            self.antiquarian.works.clear()  # has different signal behaviour
        elif method == self.REMOVE_SET_BLANK:
            self.antiquarian.works.set(Work.objects.none())  # set to empty

        # antiquarian should now have fewer links directly to it
        expected = (self.antiquarian.works.count() + 1) * self.NUM
        self.assertEqual(self.antiquarian.fragmentlinks.count(), expected)
        # for link in self.antiquarian.fragmentlinks.all():
        #     self.assertIsNone(link.work)

        # the antiquarian links have been reordered
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian=self.antiquarian)):
            self.assertEqual(count, link.order)

        # the fragment links to the works should still be there
        nfragments = Fragment.objects.count()
        nworks = Work.objects.count()

        # there should be no stray links lying around
        self.assertEqual(
            FragmentLink.objects.all().count(),
            self.NUM + nfragments * nworks
        )

        for work in Work.objects.all():
            self.assertEqual(
                FragmentLink.objects.filter(work=work).count(),
                nfragments
            )

        # check that orphaned works have been reordered
        # (with respect to blank antiquarian)
        for count, link in enumerate(
                FragmentLink.objects.filter(antiquarian__isnull=True)):
            self.assertEqual(count, link.order)


class TestLinkScheme(TestCase):

    def setUp(self):
        # add an antiquarian with a work
        self.antiquarian = Antiquarian.objects.create(
            name='name',
            re_code='name'
        )
        self.work = Work.objects.create(name='work')
        self.antiquarian.works.add(self.work)
        self.book = Book.objects.create(work=self.work, number=1)

        data = {
            'name': 'name',
        }
        self.fragment = Fragment.objects.create(**data)
        self.testimonium = Testimonium.objects.create(**data)

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
        self.assertEqual(0, len(self.fragment.definite_works_and_books()))
        self.assertEqual(0, len(self.fragment.possible_works_and_books()))
        self.assertEqual(0, self.fragment.definite_antiquarians().count())
        self.assertEqual(0, self.fragment.possible_antiquarians().count())

        link = FragmentLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            fragment=self.fragment,
            definite=True
        )

        self.assertEqual(1, len(self.fragment.definite_works_and_books()))
        self.assertEqual(0, len(self.fragment.possible_works_and_books()))
        self.assertEqual(0, self.fragment.definite_antiquarians().count())
        self.assertEqual(0, self.fragment.possible_antiquarians().count())

        link.definite = False
        link.save()

        self.assertEqual(0, len(self.fragment.definite_works_and_books()))
        self.assertEqual(1, len(self.fragment.possible_works_and_books()))
        self.assertEqual(0, self.fragment.definite_antiquarians().count())
        self.assertEqual(0, self.fragment.possible_antiquarians().count())

        link.book = self.book
        link.save()
        self.assertEqual(0, len(self.fragment.definite_works_and_books()))
        self.assertEqual(1, len(self.fragment.possible_works_and_books()))
        self.assertEqual(0, self.fragment.definite_antiquarians().count())
        self.assertEqual(0, self.fragment.possible_antiquarians().count())

        link.work = None
        link.definite = True
        link.save()

        self.assertEqual(0, len(self.fragment.definite_works_and_books()))
        self.assertEqual(0, len(self.fragment.possible_works_and_books()))
        self.assertEqual(1, self.fragment.definite_antiquarians().count())
        self.assertEqual(0, self.fragment.possible_antiquarians().count())

        link.definite = False
        link.save()

        self.assertEqual(0, len(self.fragment.definite_works_and_books()))
        self.assertEqual(0, len(self.fragment.possible_works_and_books()))
        self.assertEqual(0, self.fragment.definite_antiquarians().count())
        self.assertEqual(1, self.fragment.possible_antiquarians().count())

    def test_testimonium_queryset_methods(self):
        self.assertEqual(0, len(self.testimonium.definite_works_and_books()))
        self.assertEqual(0, len(self.testimonium.possible_works_and_books()))
        self.assertEqual(0, self.testimonium.definite_antiquarians().count())
        self.assertEqual(0, self.testimonium.possible_antiquarians().count())

        link = TestimoniumLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            testimonium=self.testimonium,
            definite=True
        )

        self.assertEqual(1, len(self.testimonium.definite_works_and_books()))
        self.assertEqual(0, len(self.testimonium.possible_works_and_books()))
        self.assertEqual(0, self.testimonium.definite_antiquarians().count())
        self.assertEqual(0, self.testimonium.possible_antiquarians().count())

        link.definite = False
        link.save()

        self.assertEqual(0, len(self.testimonium.definite_works_and_books()))
        self.assertEqual(1, len(self.testimonium.possible_works_and_books()))
        self.assertEqual(0, self.testimonium.definite_antiquarians().count())
        self.assertEqual(0, self.testimonium.possible_antiquarians().count())

        link.book = self.book
        link.save()
        self.assertEqual(0, len(self.testimonium.definite_works_and_books()))
        self.assertEqual(1, len(self.testimonium.possible_works_and_books()))
        self.assertEqual(0, self.testimonium.definite_antiquarians().count())
        self.assertEqual(0, self.testimonium.possible_antiquarians().count())

        link.work = None
        link.definite = True
        link.save()

        self.assertEqual(0, len(self.testimonium.definite_works_and_books()))
        self.assertEqual(0, len(self.testimonium.possible_works_and_books()))
        self.assertEqual(1, self.testimonium.definite_antiquarians().count())
        self.assertEqual(0, self.testimonium.possible_antiquarians().count())

        link.definite = False
        link.save()

        self.assertEqual(0, len(self.testimonium.definite_works_and_books()))
        self.assertEqual(0, len(self.testimonium.possible_works_and_books()))
        self.assertEqual(0, self.testimonium.definite_antiquarians().count())
        self.assertEqual(1, self.testimonium.possible_antiquarians().count())

    def test_add_antiquarian_fragment_ignores_work(self):
        FragmentLink.objects.create(
            antiquarian=self.antiquarian,
            work=self.work,
            fragment=self.fragment,
            definite=True
        )
        self.assertEqual(len(self.fragment.definite_works_and_books()), 1)
        # add more links to the antiquarian and the work should be unaffected
        for i in range(0, 10):
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=self.fragment,
                definite=True
            )
        self.assertEqual(len(self.fragment.definite_works_and_books()), 1)

    def test_get_all_names(self):
        # all names that this fragment is known by according to the
        # links it has with various objects
        a = Antiquarian.objects.create(name='name1', re_code='name1')
        data = {
            'name': 'name1',
        }
        fragment = Fragment.objects.create(**data)
        linkfa1 = FragmentLink.objects.create(
            fragment=fragment,
            antiquarian=a
        )
        linkfa2 = FragmentLink.objects.create(
            fragment=fragment,
            antiquarian=a
        )
        # should be ordered wrt antiquarian then order
        self.assertEqual(
            fragment.get_all_names(),
            [
                '{}'.format(linkfa1.get_display_name()),
                '{}'.format(linkfa2.get_display_name())
            ]
        )

        testimonium = Testimonium.objects.create(**data)
        linkta1 = TestimoniumLink.objects.create(
            testimonium=testimonium,
            antiquarian=a
        )
        linkta2 = TestimoniumLink.objects.create(
            testimonium=testimonium,
            antiquarian=a
        )
        # should be ordered wrt antiquarian then order
        self.assertEqual(
            testimonium.get_all_names(),
            [
                '{}'.format(linkta1.get_display_name()),
                '{}'.format(linkta2.get_display_name())
            ]
        )


class TestWorkLinkUpdateScheme(TestCase):

    def setUp(self):
        # add an antiquarian with a work
        self.antiquarian = Antiquarian.objects.create(
            name='name',
            re_code='name'
        )
        self.work = Work.objects.create(name='work')
        self.antiquarian.works.add(self.work)
        self.book = Book.objects.create(work=self.work, number=1)

        data = {
            'name': 'name',
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
            # now independently set for the antiquarian
            FragmentLink.objects.create(
                antiquarian=self.antiquarian,
                fragment=self.fragment,
            )

        # work_order should be set wrt links with a work link
        qs = FragmentLink.objects.filter(antiquarian=self.antiquarian)
        for count, link in enumerate(
                qs.filter(work__isnull=False).order_by('work_order')):
            self.assertEqual(link.work_order, count)
            self.assertEqual(link.display_work_order_one_indexed(), count + 1)

        # the links to antiquarians should be independent as before
        for count, link in enumerate(qs.order_by('order')):
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
        FragmentLink.objects.filter(pk__in=(8, 6, 3)).delete()

        # indexes should have been patched
        for count, pk in enumerate(link_pks):
            link = TestimoniumLink.objects.get(pk=pk)
            self.assertEqual(link.work_order, count)


class TestFragmentWorkOrderingScheme(TestCase):
    NUM = 5

    def setUp(self):
        # add an antiquarian with a work
        self.antiquarian = Antiquarian.objects.create(
            name='name',
            re_code='name'
        )
        self.work = Work.objects.create(name='work')
        self.antiquarian.works.add(self.work)

        for i in range(0, self.NUM):
            data = {
                'name': 'name{}'.format(i),
            }
            fragment = Fragment.objects.create(**data)

            # add links to antiquarian directly
            FragmentLink.objects.create(
                antiquarian=self.antiquarian, fragment=fragment,
                work=self.work,
                definite=True
            )

    def _get_fragment_names(self):
        return [
            link.fragment.name for link in
            self.work.antiquarian_work_fragmentlinks.order_by('work_order')
        ]

    def test_up_by_work(self):
        fragment_names = self._get_fragment_names()
        self.assertEqual(len(fragment_names), 5)
        test_link = self.work.antiquarian_work_fragmentlinks.last()

        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (0, 1, 2, 3, 4)]
        )

        test_link.up_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (0, 1, 2, 4, 3)]
        )

        test_link.up_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (0, 1, 4, 2, 3)]
        )

        test_link.up_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (0, 4, 1, 2, 3)]
        )

        test_link.up_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (4, 0, 1, 2, 3)]
        )

        # attempt to move above pos 0 has no effect and does not barf
        test_link.up_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (4, 0, 1, 2, 3)]
        )

    def test_down_by_work(self):
        fragment_names = self._get_fragment_names()
        self.assertEqual(len(fragment_names), 5)
        test_link = self.work.antiquarian_work_fragmentlinks.first()

        test_link.down_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (1, 0, 2, 3, 4)]
        )

        test_link.down_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (1, 2, 0, 3, 4)]
        )

        test_link.down_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (1, 2, 3, 0, 4)]
        )

        test_link.down_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (1, 2, 3, 4, 0)]
        )

        # attempt to move off the end has no effect and does not barf
        test_link.down_by_work()
        self.assertEqual(
            self._get_fragment_names(),
            [fragment_names[i] for i in (1, 2, 3, 4, 0)]
        )
