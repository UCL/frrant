# Generated by Django 3.1 on 2021-04-21 07:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0050_auto_20210421_0736'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='originaltext',
            options={'ordering': ('citing_work', 'reference_order')},
        ),
        migrations.RenameField(
            model_name='historicaloriginaltext',
            old_name='reference_order_new',
            new_name='reference_order',
        ),
        migrations.RenameField(
            model_name='originaltext',
            old_name='reference_order_new',
            new_name='reference_order',
        ),
    ]