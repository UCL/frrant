from django import template, urls

register = template.Library()


@register.filter
def get_detail_page(obj):
    page = obj["detail_page"]
    key = obj["key"]
    if key is None:
        return urls.reverse(page, kwargs={"slug": obj["slug_key"]})
    return urls.reverse(page, kwargs={"pk": key})
