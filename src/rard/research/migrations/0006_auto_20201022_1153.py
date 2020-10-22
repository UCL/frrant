# Generated by Django 3.1 on 2020-10-22 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0005_auto_20201020_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='antiquarian',
            name='circa',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='antiquarian',
            name='year1',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='antiquarian',
            name='year2',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='antiquarian',
            name='year_type',
            field=models.CharField(blank=True, choices=[('range', 'From/To'), ('before', 'Before'), ('after', 'After'), ('single', 'Single Year')], max_length=16),
        ),
    ]
