import difflib

import bs4
from django import template
from django.utils.safestring import mark_safe
from reversion.models import Version

register = template.Library()


@register.filter
def get_latest_version(obj):
    # reversion (delete it)
    latest = Version.objects.get_for_object(obj).first()
    return latest


@register.filter
def get_history(obj):
    # get all reversion objects for object
    return Version.objects.get_for_object(obj)


# below for simple-history
@register.filter
def render_diff(history_item):
    lines = []
    if history_item.prev_record:

        delta = history_item.diff_against(history_item.prev_record)
        for i, change in enumerate(delta.changes):
            lines.append('<em>Field: %s</em><br>' % change.field)
            old_ = bs4.BeautifulSoup(str(change.old) if change.old else '')
            new_ = bs4.BeautifulSoup(str(change.new) if change.new else '')
            for line in difflib.Differ().compare(
                list(old_.stripped_strings),
                list(new_.stripped_strings),
            ):
                # for line in difflib.Differ().compare(
                # str(change.old).splitlines(), str(change.new).splitlines()):
                # for line in difflib.unified_diff(
                #   str(change.old).splitlines(),
                #   str(change.new).splitlines()):
                lines.append('%s<br>' % line)
                if i < len(delta.changes) - 1:
                    lines.append('<hr>')
                # for line in difflib.context_diff(
                #   str(change.old).splitlines(),
                #   str(change.new).splitlines()):
                #     lines.append('%s<br>' % line)
                # lines.extend(
                #   difflib.HtmlDiff().make_file(
                #       str(change.old).splitlines(),
                #       str(change.new).splitlines()).splitlines())

    return mark_safe(''.join(lines)) or '<em>No changes to content</em>'
