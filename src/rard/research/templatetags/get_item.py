from django import template

register = template.Library()


@register.filter
def get_item(item, selector):
    return item.get(selector, "")


@register.filter
def get_item_list(item, selector):
    return item.get(selector, [])
