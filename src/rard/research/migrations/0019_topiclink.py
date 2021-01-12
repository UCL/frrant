# Generated by Django 3.1 on 2020-12-09 14:05

from django.db import migrations, models
import django.db.models.deletion


def copy_topic_links(apps, schema_editor):
    Topic = apps.get_model("research", "Topic")
    TopicLink = apps.get_model("research", "TopicLink")
    for t in Topic.objects.all():
        for count, fragment in enumerate(t.fragment_set.all()):
            TopicLink.objects.create(topic=t, fragment=fragment, order=count)


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0018_worklink'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopicLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=None, null=True)),
                ('fragment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='research.fragment')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='research.topic')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.RunPython(copy_topic_links, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='fragment',
            name='topics',
        ),
        migrations.AddField(
            model_name='fragment',
            name='topics',
            field=models.ManyToManyField(blank=True, through='research.TopicLink', to='research.Topic'),
        ),
    ]