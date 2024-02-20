# Generated by Django 3.2 on 2024-02-20 13:31

from django.db import migrations, models
import django.db.models.deletion
import rard.utils.basemodel


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0067_add_mentioned_in_fk_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicCommentaryMentions",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "content",
                    rard.utils.basemodel.DynamicTextField(blank=True, default=""),
                ),
                ("approved", models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name="anonymousfragment",
            name="public_commentary_mentions",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="public_commentary_mentions_for_anonymousfragment",
                to="research.publiccommentarymentions",
            ),
        ),
        migrations.AddField(
            model_name="fragment",
            name="public_commentary_mentions",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="public_commentary_mentions_for_fragment",
                to="research.publiccommentarymentions",
            ),
        ),
        migrations.AddField(
            model_name="historicalanonymousfragment",
            name="public_commentary_mentions",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="research.publiccommentarymentions",
            ),
        ),
        migrations.AddField(
            model_name="historicalfragment",
            name="public_commentary_mentions",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="research.publiccommentarymentions",
            ),
        ),
        migrations.AddField(
            model_name="historicaltestimonium",
            name="public_commentary_mentions",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="research.publiccommentarymentions",
            ),
        ),
        migrations.AddField(
            model_name="testimonium",
            name="public_commentary_mentions",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="public_commentary_mentions_for_testimonium",
                to="research.publiccommentarymentions",
            ),
        ),
    ]