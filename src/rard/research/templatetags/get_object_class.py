from django import template

register = template.Library()


@register.filter
def get_object_class(obj):
    # ignore builtin types
    if obj.__class__.__module__ in ("builtins", "__builtin__"):
        return ""

    # otherwise return the class name
    return obj.__class__.__name__
