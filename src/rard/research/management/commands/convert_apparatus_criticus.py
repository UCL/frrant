from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError

from rard.research.models import ApparatusCriticusItem, OriginalText


class Command(BaseCommand):

    help = 'converts old format app crit into new version'

    def handle(self, *args, **options):
        Y = 'Y'

        resp = input(
            'This will delete all new app crit items and replace '
            'them with values derived from legacy entries. Continue? %s/n ' % Y
        )
        if resp != Y:
            print('Operation cancelled')
            return

        try:
            ApparatusCriticusItem.objects.all().delete()

            qs = OriginalText.objects.filter(apparatus_criticus__isnull=False)
            count = qs.count()
            # look for original texts with app crit set
            for o in qs:
                # get the html entered which will be
                # wrapped in <p> for existing records
                # as a 'feature' of Quill
                soup = BeautifulSoup(
                    o.apparatus_criticus, features="html.parser"
                )
                # get the <p> element and extract its content
                p = soup.find('p')
                if not p:
                    continue

                content = ''.join([str(x) for x in p.children])
                # the content will be of the form
                # 1 text1 | 2 text2 | 3 text3
                # and if not, preserve what is there in a single entry
                # as they would would have needed to reformat it anyway
                for order, item in enumerate(content.split('|')):
                    # remove the preceding number and any spaces around
                    text = item.lstrip(' 0123456789').strip()
                    ApparatusCriticusItem.objects.create(
                        parent=o,
                        order=order,
                        content=text.strip()
                    )
            print('%d apparatus criticus records converted' % count)

        except Exception as err:
            raise CommandError(str(err))
