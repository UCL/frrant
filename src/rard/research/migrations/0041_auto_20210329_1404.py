# Generated by Django 3.1 on 2021-03-29 14:04

from django.db import migrations
from bs4 import BeautifulSoup


def copy_apparatus_criticuses(apps, schema_editor):
    OriginalText = apps.get_model("research", "OriginalText")
    ApparatusCriticusItem = apps.get_model("research", "ApparatusCriticusItem")

    # for all recording with existing app crit:
    for o in OriginalText.objects.filter(apparatus_criticus__isnull=False):
        # get the html entered which will be wrapped in <p> for existing records
        soup = BeautifulSoup(o.apparatus_criticus)
        # get the <p> element and extract its content
        p = soup.find('p')
        content = ''.join([str(x) for x in p.children])
        # the content will be of the form
        # 1 text1 | 2 text2 | 3 text3
        # and if not, preserve what is there in a single entry
        for order, item in enumerate(content.split('|')):
            # remove the preceding number and any spaces around
            text = item.lstrip(' 0123456789').strip()
            o.apparatus_criticus_items.create(
                order=order,
                content=text
            )
        t.save()


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0040_auto_20210329_1123'),
    ]

    operations = [
        migrations.RunPython(copy_apparatus_criticuses, migrations.RunPython.noop),
        # migrations.RemoveField(
        #     model_name='historicaloriginaltext',
        #     name='apparatus_criticus',
        # ),
        # migrations.RemoveField(
        #     model_name='originaltext',
        #     name='apparatus_criticus',
        # ),
    ]
