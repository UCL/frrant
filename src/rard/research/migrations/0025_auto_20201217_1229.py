# Generated by Django 3.1 on 2020-12-17 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0024_auto_20201216_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='anonymousfragment',
            name='collection_id',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='fragment',
            name='collection_id',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='testimonium',
            name='collection_id',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]
