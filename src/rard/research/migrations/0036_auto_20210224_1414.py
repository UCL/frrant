# Generated by Django 3.1 on 2021-02-24 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0035_auto_20210224_1210'),
    ]

    operations = [
        migrations.AddField(
            model_name='anonymousfragment',
            name='date_range',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='anonymousfragment',
            name='order_year',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='fragment',
            name='date_range',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='fragment',
            name='order_year',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='historicalanonymousfragment',
            name='date_range',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='historicalanonymousfragment',
            name='order_year',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='historicalfragment',
            name='date_range',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='historicalfragment',
            name='order_year',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
