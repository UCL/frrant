# Generated by Django 3.2 on 2023-01-05 16:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0065_m2m_bibliography_items'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bibliographyitem',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='bibliographyitem',
            name='object_id',
        ),
        migrations.RemoveField(
            model_name='historicalbibliographyitem',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='historicalbibliographyitem',
            name='object_id',
        ),
    ]
