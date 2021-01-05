from django import template

register = template.Library()


@register.filter
def show_citing_info(obj, citing_author):
    return obj.get_citing_display(citing_author)
