from django import template

register = template.Library()


@register.filter
def name_in_context(obj, work):
    return obj.get_display_name_for_work(work)
