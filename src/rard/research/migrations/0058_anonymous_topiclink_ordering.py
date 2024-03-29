# Generated by Django 3.2 on 2022-07-14 09:39

from django.db import migrations


def give_anonymoustopiclinks_order(apps, schema_editor):
    Topic = apps.get_model("research", "Topic")
    AnonymousTopicLink = apps.get_model("research", "AnonymousTopicLink")

    for topic in Topic.objects.all():
        link_qs = AnonymousTopicLink.objects.filter(
            fragment__appositumfragmentlinks_from__isnull=True,
            topic=topic
            ).order_by("fragment__order")
        for count, link in enumerate(link_qs):
            link.order = count + 1  # Start counting from 1 if not apposita
            link.save()
    # All apposita-topic links should have order 0 regardless of topic
    AnonymousTopicLink.objects.filter(
        fragment__appositumfragmentlinks_from__isnull=False
        ).update(order=0)


def reverse_give_anonymoustopiclinks_order(apps, schema_editor):
    AnonymousTopicLink = apps.get_model("research", "AnonymousTopicLink")
    AnonymousTopicLink.objects.update(order=None)

class Migration(migrations.Migration):

    dependencies = [
        ("research", "0057_reindex_testimonia_links"),
    ]

    operations = [
        migrations.RunPython(
            give_anonymoustopiclinks_order, reverse_give_anonymoustopiclinks_order
        )
    ]
