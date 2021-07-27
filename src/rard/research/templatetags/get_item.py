from django import template

register = template.Library()


@register.filter
def get_item(item, selector):
    return item.get(selector, '')
