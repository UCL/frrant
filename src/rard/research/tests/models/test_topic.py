import pytest
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify

from rard.research.models import Fragment, Topic

pytestmark = pytest.mark.django_db


class TestTopic(TestCase):
    def test_creation(self):
        # check we can create
        topic = Topic.objects.create(name="name")
        self.assertTrue(Topic.objects.filter(pk=topic.pk).exists())

    def test_required_fields(self):
        self.assertFalse(Topic._meta.get_field("name").blank)

    def test_display(self):
        # the __str__ function should show the name
        name = "the_name"
        topic = Topic.objects.create(name=name)
        self.assertEqual(str(topic), name)

    def test_name_unique(self):
        name = "the_name"
        Topic.objects.create(name=name)
        with self.assertRaises(IntegrityError):
            Topic.objects.create(name=name)

    def test_slug_field(self):
        name = "Some Name or Other"
        topic = Topic.objects.create(name=name)
        self.assertEqual(topic.slug, slugify(name))
        new_name = "We Have Changed the Name"
        topic.name = new_name
        topic.save()
        self.assertEqual(topic.slug, slugify(new_name))

    def test_slug_field_handles_unicode(self):
        name = "\u1234"
        topic = Topic.objects.create(name=name)
        # as we can't make a slug from unicode
        # we set the slug to be the pk value
        self.assertEqual(topic.name, name)
        self.assertEqual(topic.slug, str(topic.pk))

    def test_fragment_can_have_multiple_topics(self):
        fragment = Fragment.objects.create(name="name")
        length = 10
        for i in range(0, length):
            topic = Topic.objects.create(name="Topic %d" % i)
            fragment.topics.add(topic)
        self.assertEqual(fragment.topics.count(), length)

    def test_topic_can_belong_to_multiple_fragments(self):
        topic = Topic.objects.create(name="The Topic")
        length = 10
        for i in range(0, length):
            fragment = Fragment.objects.create(name="name{}".format(i))
            fragment.topics.add(topic)
        self.assertEqual(topic.fragment_set.count(), length)

    def test_deleting_topic_leaves_fragment(self):
        fragment = Fragment.objects.create(name="name")
        topic = Topic.objects.create(name="The Topic")
        fragment.topics.add(topic)
        fragment_pk = fragment.pk
        # delete the topic
        topic.delete()
        # we should still have the fragment
        Fragment.objects.get(pk=fragment_pk)

    def test_deleting_fragment_leaves_topic(self):
        fragment = Fragment.objects.create(name="name")
        topic = Topic.objects.create(name="The Topic")
        fragment.topics.add(topic)
        topic_pk = topic.pk
        # delete the fragment
        fragment.delete()
        # we should still have the topic
        Topic.objects.get(pk=topic_pk)

    def test_ordering(self):
        names = [
            "Science",
            "Art",
            "Politics",
            "Carpentry",
        ]
        for counter, name in enumerate(names):
            Topic.objects.create(name=name, order=counter)

        db_names = []
        for a in Topic.objects.all():
            db_names.append(a.name)

        # regardless of the name, the ordering should be used
        self.assertEqual(db_names, names)

    def test_get_absolute_url(self):
        name = "the_name"
        topic = Topic.objects.create(name=name)
        self.assertEqual(
            topic.get_absolute_url(),
            reverse("topic:detail", kwargs={"slug": topic.slug}),
        )

    def test_move_up(self):
        names = [
            "Science",
            "Art",
            "Politics",
            "Carpentry",
        ]
        for counter, name in enumerate(names):
            Topic.objects.create(name=name, order=counter)

        self.assertEqual([x.name for x in Topic.objects.all()], names)

        t = Topic.objects.last()
        t.up()

        self.assertEqual(
            [x.name for x in Topic.objects.all()],
            [
                "Science",
                "Art",
                "Carpentry",
                "Politics",
            ],
        )

    def test_move_down(self):
        names = [
            "Science",
            "Art",
            "Politics",
            "Carpentry",
        ]
        for counter, name in enumerate(names):
            Topic.objects.create(name=name, order=counter)

        self.assertEqual([x.name for x in Topic.objects.all()], names)

        t = Topic.objects.first()
        t.down()

        self.assertEqual(
            [x.name for x in Topic.objects.all()],
            [
                "Art",
                "Science",
                "Politics",
                "Carpentry",
            ],
        )
