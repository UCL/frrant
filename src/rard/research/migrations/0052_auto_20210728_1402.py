# Generated by Django 3.1 on 2021-07-28 14:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0051_auto_20210421_0741'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appositumfragmentlink',
            name='book',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='antiquarian_book_appositumfragmentlinks', to='research.book'),
        ),
        migrations.AlterField(
            model_name='fragmentlink',
            name='book',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='antiquarian_book_fragmentlinks', to='research.book'),
        ),
        migrations.AlterField(
            model_name='testimoniumlink',
            name='book',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='antiquarian_book_testimoniumlinks', to='research.book'),
        ),
    ]
