from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0071_add_duplicates_field"),
    ]


operations = [
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
        model_name="testimonium",
        name="duplicate_afs",
        field=models.ManyToManyField(
            blank=True,
            related_name="testimonium_duplicate_anonfragments",
            to="research.AnonymousFragment",
        ),
    ),
    migrations.AddField(
        model_name="anonymousfragment",
        name="duplicate_ts",
        field=models.ManyToManyField(
            blank=True,
            related_name="anonymousfragment_duplicate_ts",
            to="research.Testimonium",
        ),
    ),
    migrations.AddField(
        model_name="fragment",
        name="duplicate_ts",
        field=models.ManyToManyField(
            blank=True,
            related_name="fragment_duplicate_ts",
            to="research.Testimonium",
        ),
    ),
    migrations.AddField(
        model_name="testimonium",
        name="duplicate_ts",
        field=models.ManyToManyField(
            blank=True,
            related_name="testimonium_duplicate_ts",
            to="research.Testimonium",
        ),
    ),
]
