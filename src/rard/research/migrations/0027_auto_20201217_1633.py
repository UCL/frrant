# Generated by Django 3.1 on 2020-12-17 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0026_auto_20201217_1603'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='topic',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='topic',
            name='order',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='worklink',
            name='order',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]
