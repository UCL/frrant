# Generated by Django 3.2 on 2022-08-25 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0058_anonymous_topiclink_ordering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaloriginaltext',
            name='reference',
            field=models.CharField(default='temp', max_length=128),
        ),
        migrations.AlterField(
            model_name='originaltext',
            name='reference',
            field=models.CharField(default='temp', max_length=128),
        ),
    ]
