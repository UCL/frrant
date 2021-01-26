# Generated by Django 3.1 on 2021-01-22 17:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import rard.research.models.history


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0033_historicalobjects'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalRecordLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('history_date', models.DateTimeField(editable=False)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('history_user', models.ForeignKey(default=None, null=True, on_delete=models.SET(rard.research.models.history.HistoricalRecordLog.get_sentinel_user), related_name='history_log', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['history_date'],
            },
        ),
    ]
