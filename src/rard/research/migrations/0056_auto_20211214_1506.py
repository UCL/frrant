# Generated by Django 3.2 on 2021-12-14 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0055_auto_20211202_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaloriginaltext',
            name='plain_content',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='historicaltranslation',
            name='plain_translated_text',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='originaltext',
            name='plain_content',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='translation',
            name='plain_translated_text',
            field=models.TextField(default=''),
        ),
    ]