# Generated by Django 3.2 on 2024-03-07 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0069_anonymousfragment_anonymous_fragments"),
    ]

    operations = [
        migrations.AddField(
            model_name="anonymousfragment",
            name="duplicate_frags",
            field=models.ManyToManyField(
                blank=True,
                related_name="anonymousfragment_duplicate_fragments",
                to="research.Fragment",
            ),
        ),
        migrations.AddField(
            model_name="fragment",
            name="duplicate_frags",
            field=models.ManyToManyField(
                blank=True,
                related_name="fragment_duplicate_fragments",
                to="research.Fragment",
            ),
        ),
        # Currently this isn't utilised but as HistoricalBase is abstract it's part of the migration
        migrations.AddField(
            model_name="testimonium",
            name="duplicate_frags",
            field=models.ManyToManyField(
                blank=True,
                related_name="testimonium_duplicate_fragments",
                to="research.Fragment",
            ),
        ),
        migrations.AddField(
            model_name="anonymousfragment",
            name="duplicate_afs",
            field=models.ManyToManyField(
                blank=True,
                related_name="anonymousfragment_duplicate_anonfragments",
                to="research.AnonymousFragment",
            ),
        ),
        migrations.AddField(
            model_name="fragment",
            name="duplicate_afs",
            field=models.ManyToManyField(
                blank=True,
                related_name="fragment_duplicate_anonfragments",
                to="research.AnonymousFragment",
            ),
        ),
        # Currently this isn't utilised but as HistoricalBase is abstract it's part of the migration
        migrations.AddField(
            model_name="testimonium",
            name="duplicate_afs",
            field=models.ManyToManyField(
                blank=True,
                related_name="testimonium_duplicate_anonfragments",
                to="research.AnonymousFragment",
            ),
        ),
    ]
