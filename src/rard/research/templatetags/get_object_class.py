from django import template

register = template.Library()


@register.filter
def get_object_class(obj):
    try:
        return obj.__class__.__name__
    except AttributeError:
        return ''
