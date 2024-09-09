# Generated by Django 3.2 on 2024-07-02 11:07

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import rard.research.models.mixins

import csv


def import_data_from_csv(apps, schema_editor):
    file_path = "rard/research/migrations/data/concordance_starter_values.csv"
    with open(file_path, "r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            edition_name = row["EditionIdentifier"]
            part_identifier_value = row["PartIdentifier"]
            description = row["Description"]
            # Create or get Edition instance
            Edition = apps.get_model("research", "Edition")
            edition, created = Edition.objects.get_or_create(
                name=edition_name, description=description
            )

            # Create PartIdentifier instance associated with Edition
            PartIdentifier = apps.get_model("research", "PartIdentifier")
            PartIdentifier.objects.create(edition=edition, value=part_identifier_value)


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0072_adding_testimonia_duplicates"),
    ]

    operations = [
        migrations.CreateModel(
            name="Edition",
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
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                (
                    "description",
                    models.CharField(max_length=200, blank=True, null=True),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(rard.research.models.mixins.HistoryModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="PartIdentifier",
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
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("value", models.CharField(max_length=250)),
                ("display_order", models.CharField(blank=True, max_length=30)),
                (
                    "edition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="research.edition",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(rard.research.models.mixins.HistoryModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ConcordanceModel",
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
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "content_type",
                    models.CharField(
                        choices=[
                            ("F", "Fragment"),
                            ("T", "Testimonium"),
                            ("App", "Appendix"),
                            ("P.", "Pagination"),
                            ("NA", "N/A"),
                        ],
                        max_length=5,
                    ),
                ),
                ("reference", models.CharField(blank=True, max_length=15)),
                ("concordance_order", models.CharField(max_length=15, blank=True)),
                (
                    "identifier",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="research.partidentifier",
                    ),
                ),
                (
                    "original_text",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="concordance_models",
                        to="research.originaltext",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(rard.research.models.mixins.HistoryModelMixin, models.Model),
        ),
        migrations.RunPython(import_data_from_csv, migrations.RunPython.noop),
    ]
