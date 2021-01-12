# Generated by Django 3.1 on 2020-12-14 16:26

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import rard.research.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0020_auto_20201210_1617'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnonymousFragment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=128)),
                ('order', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('commentary', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='commentary_for_anonymousfragment', to='research.textobjectfield')),
                ('images', models.ManyToManyField(blank=True, to='research.Image')),
                ('topics', models.ManyToManyField(blank=True, to='research.Topic')),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
            },
            bases=(rard.research.models.mixins.TextObjectFieldMixin, models.Model),
        ),
        migrations.CreateModel(
            name='AnonymousFragmentLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('order', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('definite', models.BooleanField(default=False)),
                ('work_order', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('antiquarian', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='anonymousfragmentlinks', to='research.antiquarian')),
                ('book', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='antiquarian_book_anonymousfragmentlinks', to='research.book')),
                ('fragment', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='antiquarian_anonymousfragmentlinks', to='research.anonymousfragment')),
                ('work', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='antiquarian_work_anonymousfragmentlinks', to='research.work')),
            ],
            options={
                'ordering': ['order'],
                'abstract': False,
            },
        ),
    ]