# Generated by Django 3.2 on 2023-06-23 09:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0063_work_book_introductions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="antiquarian",
            name="introduction",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="introduction_for_antiquarian",
                to="research.textobjectfield",
            ),
        ),
        migrations.AlterField(
            model_name="historicalbook",
            name="introduction",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="introduction_for_historicalbook",
                to="research.textobjectfield",
            ),
        ),
        migrations.AlterField(
            model_name="historicalwork",
            name="introduction",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="introduction_for_historicalwork",
                to="research.textobjectfield",
            ),
        ),
    ]
