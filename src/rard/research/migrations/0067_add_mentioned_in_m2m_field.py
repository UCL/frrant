# Generated by Django 3.2 on 2024-01-24 11:48

import bs4
from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations, models, IntegrityError
from psycopg2 import errors


def get_fragment_testimonia_mentions(text_obj, apps):
    """This finds all mentions of (A)F&T, identifies the
    original objects and returns them as a list"""

    soup = bs4.BeautifulSoup(text_obj.content, features="html.parser")
    mentions = soup.find_all("span", class_="mention")
    valid_models = ["fragment", "anonymousfragment", "testimonium"]
    linked_items = []
    for item in mentions:
        model = item.attrs.get("data-target", None)
        pk = item.attrs.get("data-id", None)
        if model in valid_models and pk:
            try:
                model = apps.get_model(app_label="research", model_name=model)
                m = model.objects.get(pk=int(pk))
                linked_items.append(m)
            except ObjectDoesNotExist:
                pass
    return linked_items


def set_mentions(text_obj, apps):
    found_mention_items = get_fragment_testimonia_mentions(text_obj, apps)
    text_obj.fragment_testimonia_mentions = []
    for item in found_mention_items:
        if text_obj not in item.mentioned_in.all():
            try:
                item.mentioned_in.add(text_obj)
                text_obj.fragment_testimonia_mentions.append(item)
            except IntegrityError as e:
                if isinstance(e.__cause__, errors.UniqueViolation):
                    print(f"Duplicate entry detected: {e}")
                    pass
                else:
                    raise
    return text_obj.fragment_testimonia_mentions


def update_mentions(apps, schema_editor):
    TextObjectField = apps.get_model("research", "TextObjectField")
    # this should trigger the mentions to be generated
    for text_object in TextObjectField.objects.all():
        set_mentions(text_object, apps)


class Migration(migrations.Migration):
    dependencies = [
        ("research", "0066_remove_bibliography_item_gfk"),
    ]

    operations = [
        migrations.AddField(
            model_name="anonymousfragment",
            name="mentioned_in",
            field=models.ManyToManyField(
                blank=True,
                to="research.TextObjectField",
                related_name="%(class)s_mentions",
            ),
        ),
        migrations.AddField(
            model_name="fragment",
            name="mentioned_in",
            field=models.ManyToManyField(
                blank=True,
                to="research.TextObjectField",
                related_name="%(class)s_mentions",
            ),
        ),
        migrations.AddField(
            model_name="testimonium",
            name="mentioned_in",
            field=models.ManyToManyField(
                blank=True,
                to="research.TextObjectField",
                related_name="%(class)s_mentions",
            ),
        ),
        migrations.RunPython(update_mentions, migrations.RunPython.noop),
    ]
