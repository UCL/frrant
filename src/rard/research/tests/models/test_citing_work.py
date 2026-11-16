import pytest
from django.test import TestCase

from rard.research.models import (
    AnonymousFragment,
    CitingAuthor,
    CitingWork,
    Fragment,
    Testimonium,
)

pytestmark = pytest.mark.django_db


class TestCitingWork(TestCase):
    def test_creation(self):
        # check we can create with just title
        citing_work = CitingWork.objects.create(title="title")
        self.assertTrue(CitingWork.objects.filter(pk=citing_work.pk).exists())
        # check introduction also created
        self.assertIsNotNone(CitingWork.objects.get(pk=citing_work.pk).introduction.pk)

    def test_required_fields(self):
        self.assertFalse(CitingWork._meta.get_field("title").blank)
        self.assertTrue(CitingWork._meta.get_field("author").blank)
        self.assertTrue(CitingWork._meta.get_field("edition").blank)

    def test_display(self):
        # the __str__ function
        title = "the_title"
        citing_work = CitingWork.objects.create(title=title)
        self.assertEqual("Anonymous, {}".format(title), str(citing_work))

        # add an author and we should see that
        name = "Bob"
        author = CitingAuthor(name=name)
        citing_work.author = author
        self.assertEqual("{}, {}".format(name, title), str(citing_work))

    def test_fragments(self):
        citing_work = CitingWork.objects.create(title="citing_work")
        for i in range(0, 10):
            fragment = Fragment.objects.create()
            # create original text linked to this citing work
            fragment.original_texts.create(citing_work=citing_work)
        self.assertEqual(
            [x.pk for x in Fragment.objects.all()],
            [x.pk for x in citing_work.fragments()],
        )

    def test_fragments_distinct(self):
        # linking multiple original texts within a testimonium
        # to a single citing work should result in a single link
        citing_work = CitingWork.objects.create(title="citing_work")
        fragment = Fragment.objects.create()
        for i in range(0, 10):
            # create original text linked to this citing work
            fragment.original_texts.create(citing_work=citing_work)
        self.assertEqual(1, citing_work.fragments().count())

    def test_testimonia(self):
        citing_work = CitingWork.objects.create(title="citing_work")
        for i in range(0, 10):
            testimonium = Testimonium.objects.create()
            # create original text linked to this citing work
            testimonium.original_texts.create(citing_work=citing_work)
        self.assertEqual(
            [x.pk for x in Testimonium.objects.all()],
            [x.pk for x in citing_work.testimonia()],
        )

    def test_testimonia_distinct(self):
        # linking multiple original texts within a testimonium
        # to a single citing work should result in a single link
        citing_work = CitingWork.objects.create(title="citing_work")
        testimonium = Testimonium.objects.create()
        for i in range(0, 10):
            # create original text linked to this citing work
            testimonium.original_texts.create(citing_work=citing_work)
        self.assertEqual(1, citing_work.testimonia().count())


class TestCitingAuthor(TestCase):
    def test_creation(self):
        # check we can create with just title
        author = CitingAuthor.objects.create(name="name")
        self.assertTrue(CitingAuthor.objects.filter(pk=author.pk).exists())
        # check introduction also created
        self.assertIsNotNone(CitingAuthor.objects.get(pk=author.pk).introduction.pk)

    def test_required_fields(self):
        self.assertFalse(CitingAuthor._meta.get_field("name").blank)

    def test_display(self):
        # the __str__ function
        name = "Bob"
        author = CitingAuthor(name=name)
        self.assertEqual(name, str(author))

    def test_ordered_materials(self):
        author = CitingAuthor.objects.create(name="name")
        citing_work1 = CitingWork.objects.create(author=author, title="citing_work")
        citing_work2 = CitingWork.objects.create(author=author, title="citing_work")
        fragment = Fragment.objects.create()
        fragment.original_texts.create(citing_work=citing_work1)

        testimonium = Testimonium.objects.create()
        testimonium.original_texts.create(citing_work=citing_work2)

        anon = AnonymousFragment.objects.create()
        anon.original_texts.create(citing_work=citing_work2)
        fragment.apposita.add(anon)

        materials = author.ordered_materials()

        self.assertEqual([x.pk for x in materials["testimonia"]], [testimonium.pk])
        self.assertEqual([x.pk for x in materials["fragments"]], [fragment.pk])
        self.assertEqual([x.pk for x in materials["apposita"]], [anon.pk])
