# Generated by Django 3.2 on 2023-04-19 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("research", "0061_order_in_book"),
    ]
    # the definite field for each link will be converted to definite_antiquarian.
    # Definite work and book fields will be added
    operations = [
        migrations.AlterModelOptions(
            name="book",
            options={"ordering": ["unknown", "order", "number"]},
        ),
        migrations.AlterModelOptions(
            name="worklink",
            options={"ordering": ["work__unknown", "order"]},
        ),
        migrations.RenameField(
            model_name="appositumfragmentlink",
            old_name="definite",
            new_name="definite_antiquarian",
        ),
        migrations.RenameField(
            model_name="fragmentlink",
            old_name="definite",
            new_name="definite_antiquarian",
        ),
        migrations.RenameField(
            model_name="testimoniumlink",
            old_name="definite",
            new_name="definite_antiquarian",
        ),
        migrations.AddField(
            model_name="appositumfragmentlink",
            name="definite_book",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appositumfragmentlink",
            name="definite_work",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="fragmentlink",
            name="definite_book",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="fragmentlink",
            name="definite_work",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="testimoniumlink",
            name="definite_book",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="testimoniumlink",
            name="definite_work",
            field=models.BooleanField(default=False),
        ),
    ]
