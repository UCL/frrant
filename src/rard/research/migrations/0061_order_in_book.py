# Generated by Django 3.2 on 2023-01-23 11:20

from django.db import migrations, models
import itertools


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0060_add_reference_model"),
    ]

    def create_unknown_work(apps, schema_editor):
        Antiquarian = apps.get_model("research", "Antiquarian")
        Work = apps.get_model("research", "Work")

        antiquarians = Antiquarian.objects.all()
        for ant in antiquarians:
            ant.works.add(Work.objects.create(name="Unknown Work", unknown=True))

    def create_unknown_book(apps, schema_editor):
        Work = apps.get_model("research", "Work")
        works = Work.objects.all()
        for work in works:
            work.book_set.create(subtitle="Unknown Book", unknown=True)

    def assign_links_to_unknown(apps, schema_editor):
        worklinks = ["FragmentLink", "TestimoniumLink", "AppositumFragmentLink"]

        for link_type in worklinks:
            link_class = apps.get_model("research", link_type)
            links = link_class.objects.all()
            for link in links:
                ant = link.antiquarian
                if link.work is None:
                    link.work = ant.works.get(unknown=True)
                work = link.work
                if link.book is None:
                    link.book = work.book_set.get(unknown=True)
                link.save()

    def give_books_order(apps, schema_editor):
        Work = apps.get_model("research", "Work")
        for work in Work.objects.all():
            books = work.book_set.all().order_by("unknown", "number")
            for count, book in enumerate(books):
                book.order = count
                book.save()

    def give_links_order_in_book(apps, schema_editor):
        """As a starting point, order_in_book, will inherit its order from work_order;
        i.e. if link A precedes link B in work_order, it will precede link B in order_in_book
        if both belong to the same Book."""

        worklinks = ["FragmentLink", "TestimoniumLink", "AppositumFragmentLink"]

        Book = apps.get_model("research", "Book")

        def order_in_book_for_link_class(link_classname):
            link_class = apps.get_model("research", link_classname)
            for book in Book.objects.all():
                related_links = link_class.objects.filter(book=book).order_by(
                    "work_order"
                )
                for count, link in enumerate(related_links):
                    link.order_in_book = count
                    link.save()

        for link in worklinks:
            order_in_book_for_link_class(link)

    def reindex_links(apps, schema_editor):
        """A link's order represents its order wrt the Antiquarian. This is derived first of all
        from the order of the link's work wrt the Antiquarian, then from the link's order with
        respect to the work (work_order). Work order is derived in turn from the order of
        the link's book with respect to the Work, and then the link's order within that book.

        We now need to loop through each Work and recalculate work_order from the new
        order_in_book and book__order properties that have been added. Then we can
        loop through each Antiquarian and recalculate each related link's order based on
        work__worklink__order and work_order.

        Note: Testimonia belonging to unknown works are ordered before those belonging to
        known works; however the opposite is true for all other link classes."""

        worklinks = ["FragmentLink", "TestimoniumLink", "AppositumFragmentLink"]

        Work = apps.get_model("research", "Work")
        Antiquarian = apps.get_model("research", "Antiquarian")

        def reindex_links_to_work(work):
            for class_name in worklinks:
                link_class = apps.get_model("research", class_name)

                # Unknown book's links should always be last unless
                # Then order by book order, then order in book
                to_reorder = (
                    link_class.objects.filter(work=work)
                    .order_by("book__unknown", "book__order", "order_in_book")
                    .distinct()
                )

                for count, link in enumerate(to_reorder):
                    if link.work_order != count:
                        link.work_order = count
                        link.save()

        def reindex_links_to_antiquarian(antiquarian):
            for class_name in worklinks:
                link_class = apps.get_model("research", class_name)

                if class_name == "TestimoniumLink":
                    to_reorder = (
                        link_class.objects.filter(antiquarian=antiquarian)
                        .order_by("-work__unknown", "work__worklink__order","work_order")
                        .distinct()
                    )
                else:
                    to_reorder = (
                        link_class.objects.filter(antiquarian=antiquarian)
                        .order_by("work__unknown", "work__worklink__order","work_order")
                        .distinct()
                    )

                for count, link in enumerate(to_reorder):
                    if link.order != count:
                        link.order = count
                        link.save()

        for work in Work.objects.all():
            reindex_links_to_work(work)

        for ant in Antiquarian.objects.all():
            reindex_links_to_antiquarian(ant)


    operations = [
        migrations.AddField(
            model_name="historicalbook",
            name="unknown",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="historicalwork",
            name="unknown",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="work",
            name="unknown",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="book",
            name="unknown",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appositumfragmentlink",
            name="order_in_book",
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="book",
            name="order",
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="fragmentlink",
            name="order_in_book",
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="historicalbook",
            name="order",
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="testimoniumlink",
            name="order_in_book",
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.RunPython(create_unknown_work),
        migrations.RunPython(create_unknown_book),
        migrations.RunPython(assign_links_to_unknown),
        migrations.RunPython(give_books_order),
        migrations.RunPython(give_links_order_in_book),
        migrations.RunPython(reindex_links),
        migrations.AlterModelOptions(
            name='book',
            options={'ordering': ['unknown', 'order']},
        ),
        migrations.AlterModelOptions(
            name='worklink',
            options={'ordering': ['work__unknown', 'order']},
        ),
    ]
