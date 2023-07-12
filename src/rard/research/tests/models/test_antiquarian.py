import pytest
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    Book,
    Fragment,
    Testimonium,
    TextObjectField,
    Work,
)
from rard.research.models.antiquarian import WorkLink
from rard.research.models.base import FragmentLink, TestimoniumLink

pytestmark = pytest.mark.django_db


class TestAntiquarian(TestCase):
    def test_creation(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian.objects.create(**data)
        for key, value in data.items():
            self.assertEqual(getattr(a, key), value)

    def test_required_fields(self):
        self.assertFalse(Antiquarian._meta.get_field("name").blank)
        self.assertFalse(Antiquarian._meta.get_field("re_code").blank)
        self.assertTrue(Antiquarian._meta.get_field("works").blank)

    def test_unique_re_code(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        Antiquarian.objects.create(**data)
        # creating the same re code again should raise db error
        with self.assertRaises(IntegrityError):
            Antiquarian.objects.create(**data)

    def test_display(self):
        # the __str__ function should show the name
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian(**data)
        self.assertEqual(str(a), data["name"])

    def test_no_initial_works(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian.objects.create(**data)
        self.assertEqual(a.works.filter(unknown=False).count(), 0)

    def test_can_have_multiple_works(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian.objects.create(**data)
        length = 10
        for _ in range(0, length):
            a.works.create(name="name")
        self.assertEqual(a.works.filter(unknown=False).count(), length)

    def test_introduction_created_with_antiquarian(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian.objects.create(**data)
        self.assertIsNotNone(a.introduction.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=a.introduction.pk), a.introduction
        )

    def test_introduction_deleted_with_antiquarian(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian.objects.create(**data)
        introduction_pk = a.introduction.pk
        a.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=introduction_pk)

    def test_order_name_instantiated_on_create(self):
        # in the absence of anything else, we copy the name into the
        # order name
        a = Antiquarian.objects.create(name="Zippy", re_code="001")
        self.assertEqual(a.order_name, a.name)

        # unless we state it explicitly
        b = Antiquarian.objects.create(
            name="Bungle Bear", order_name="Bear", re_code="002"
        )
        self.assertEqual(b.order_name, "Bear")

    def test_order_by_name(self):
        names = [
            "Zippy",
            "George",
            "Bungle",
            "Geoffrey",
        ]
        for counter, name in enumerate(names):
            Antiquarian.objects.create(name=name, re_code="code{}".format(counter))

        db_names = []
        for a in Antiquarian.objects.all():
            db_names.append(a.name)

        self.assertEqual(db_names, sorted(names))

    def test_order_by_order_name(self):
        names = [
            "Zippy",
            "George",
            "Bungle",
            "Geoffrey",
        ]
        # but sort them by these...
        order_names = ["aaa", "bbb", "ccc", "ddd"]
        for counter, name in enumerate(names):
            Antiquarian.objects.create(
                name=name,
                order_name=order_names[counter],
                re_code="code{}".format(counter),
            )

        db_order_names = []
        for a in Antiquarian.objects.all():
            db_order_names.append(a.order_name)

        self.assertEqual(db_order_names, sorted(order_names))

    def test_get_absolute_url(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian.objects.create(**data)
        self.assertEqual(
            a.get_absolute_url(), reverse("antiquarian:detail", kwargs={"pk": a.pk})
        )

    def test_display_date_range(self):
        data = {"name": "John Smith", "re_code": "smitre001"}
        a = Antiquarian.objects.create(**data)
        # check the default with nothing set
        self.assertEqual(a.display_date_range(), "")
        DATE_RANGE = "From then till now"
        a.date_range = DATE_RANGE
        self.assertEqual(a.display_date_range(), DATE_RANGE)

    def test_refresh_bibliography_items_from_mentions(self):
        """If the TextObjectFields belonging to objects that are
        linked to an Antiquarian contain mentions of bibliography
        items, those bibliography items should be linked to
        the antiquarian.

        Related TextObjectFields:
        - fragment__commentary
        - testimonium__commentary
        - appositum__commentary
        - work__introduction
        - work__book__introduction
        """

        def mention_bibliography_item_in_text_object_field(bib: BibliographyItem, obj):
            if obj._meta.model_name in ["fragment", "testimonium", "anonymousfragment"]:
                tof = obj.commentary
            if obj._meta.model_name in ["antiquarian", "work", "book"]:
                tof = obj.introduction
            mention_text = f"""
                <span class="mention"
                    data-denotation-char="@"
                    data-id="{bib.pk}"
                    data-target="{bib._meta.model_name}"
                    data-value="{bib.__str__()}">
                    <span contenteditable="false">
                        <span class="ql-mention-denotation-char">
                        @
                        </span>
                        {bib.__str__()}
                    </span>
                </span>"""
            tof.content += mention_text
            tof.save()
            obj.save()

        # Start with an Antiquarian and a linked bibliography item
        aq1 = Antiquarian.objects.create(name="aq1", re_code="smitre001")
        bib_init = BibliographyItem.objects.create(
            authors="Alice Last-Name, Bob Surname",
            author_surnames="Last-Name, Surname",
            year="2023",
            title="Initial bib",
        )
        aq1.bibliography_items.add(bib_init)
        aq1.save()
        self.assertQuerysetEqual(aq1.bibliography_items.all(), [bib_init])

        fr1 = Fragment.objects.create(name="fr1")
        fr2 = Fragment.objects.create(name="fr2")
        tt1 = Testimonium.objects.create(name="tt1")
        tt2 = Testimonium.objects.create(name="tt2")
        an1 = AnonymousFragment.objects.create(name="an1")
        an2 = AnonymousFragment.objects.create(name="an2")
        wk1 = Work.objects.create(name="wk1")
        wk2 = Work.objects.create(name="wk2")
        bk1 = Book.objects.create(number="1", subtitle="bk1", work=wk1)
        bk2 = Book.objects.create(number="1", subtitle="bk1", work=wk2)
        # Link fr1, an1, tt1, and wk1 to Antiquarian aq1
        fr1.apposita.add(an1)
        FragmentLink.objects.create(antiquarian=aq1, fragment=fr1)
        TestimoniumLink.objects.create(antiquarian=aq1, testimonium=tt1)
        aq1.works.add(wk1)
        # Add bibliography item mentions to all items
        mentioners = [aq1, fr1, an1, tt1, wk1, bk1, fr2, tt2, an2, wk2, bk2]
        target_bibs = []
        for i, obj in enumerate(mentioners):
            bib = BibliographyItem.objects.create(
                authors="Alice Last-Name, Bob Surname",
                author_surnames="Last-Name, Surname",
                year="2023",
                title=f"bib_item_{i}",
            )
            mention_bibliography_item_in_text_object_field(bib=bib, obj=obj)
            # We expect the first four to be linked
            if i < 6:
                target_bibs.append(bib)
        # Now refresh antiquarian bibliography item links
        aq1.refresh_bibliography_items_from_mentions()

        # bib init should have been removed, and all those mentioned by related
        # objects should be added.
        self.assertQuerysetEqual(aq1.bibliography_items.all(), target_bibs)


class TestWorkLink(TestCase):
    def test_related_queryset(self):
        a1 = Antiquarian.objects.create(name="John", re_code="001")
        a2 = Antiquarian.objects.create(name="John", re_code="002")

        w = Work.objects.create(name="work name")
        # create worklinks for both antiquarians
        for i in range(0, 10):
            WorkLink.objects.create(antiquarian=a1, work=w)
            WorkLink.objects.create(antiquarian=a2, work=w)

        # now for each worklink, check its related queryset contains
        # only links for its own antiquarian
        for link in WorkLink.objects.all():
            for rel in link.related_queryset():
                self.assertEqual(rel.antiquarian, link.antiquarian)
