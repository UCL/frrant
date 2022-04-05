from copy import copy

from django import template

register = template.Library()


@register.filter
def get_full_path_with_page(request, page):
    params = copy(request.GET)
    get_string = params.urlencode()
    get_string += f"&page={page}"
    return "{}?{}".format(request.path, get_string)
