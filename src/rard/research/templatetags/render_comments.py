from bs4 import BeautifulSoup
from django import template
from django.template.loader import render_to_string

from rard.research.models import Comment

register = template.Library()


@register.filter
def render_comments(value):
    print('value %s' % value)
    soup = BeautifulSoup(value)
    comments = soup.findAll("span", {"class": "comment"})
    for comment in comments:
        pk = comment['data-comment']
        try:
            obj = Comment.objects.get(pk=int(pk))
            comment['data-toggle'] = 'tooltip'
            # comment['data-toggle'] = 'popover'
            comment['data-html'] = 'true'
            render_context = {
                'comment': obj
            }
            content = render_to_string(
                'research/partials/comment_tooltip.html', render_context
            )
            # content = render_to_string(
            #     'research/partials/comment_list_item.html', render_context
            # )
            comment['title'] = content
            # comment['data-content'] = content
            # comment['data-placement'] = 'top'
            # comment['data-trigger'] = 'hover'
            # comment['title'] = '<p>{}</p> <small>{}</small>'
            # .format(obj.content, obj.user.display_name())
        except Comment.DoesNotExist:
            pass
    return soup
