# Generated by Django 3.1 on 2021-03-23 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0043_auto_20210322_0952'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='citingauthor',
            options={'ordering': ('order_name',)},
        ),
    ]
