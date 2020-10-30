from copy import copy

from django import template

register = template.Library()


@register.filter
def get_full_path_with_page(request, page):
    params = copy(request.GET)
    params['page'] = page
    get_string = '&'.join(
        ['{}={}'.format(k, v) for k, v in params.items()]
    )
    return '{}?{}'.format(request.path, get_string)
