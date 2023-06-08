import difflib

import bs4
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


# below for simple-history
@register.filter
def render_diff(history_item):
    lines = []
    if history_item.prev_record:
        delta = history_item.diff_against(history_item.prev_record)
        for i, change in enumerate(delta.changes):
            lines.append("<em>Field: %s</em><br>" % change.field)
            old_ = bs4.BeautifulSoup(str(change.old) if change.old else "")
            new_ = bs4.BeautifulSoup(str(change.new) if change.new else "")
            for line in difflib.Differ().compare(
                list(old_.stripped_strings),
                list(new_.stripped_strings),
            ):
                if line.find("?") == 0:
                    # ignore the intraline indicators that attempt to show
                    # where in the line the difference happens
                    continue
                # for line in difflib.Differ().compare(
                # str(change.old).splitlines(), str(change.new).splitlines()):
                # for line in difflib.unified_diff(
                #   str(change.old).splitlines(),
                #   str(change.new).splitlines()):
                lines.append("%s<br>" % line)
                if i < len(delta.changes) - 1:
                    lines.append("<hr>")
                # for line in difflib.context_diff(
                #   str(change.old).splitlines(),
                #   str(change.new).splitlines()):
                #     lines.append('%s<br>' % line)
                # lines.extend(
                #   difflib.HtmlDiff().make_file(
                #       str(change.old).splitlines(),
                #       str(change.new).splitlines()).splitlines())

    return mark_safe("".join(lines)) or "<em>No changes to content</em>"
