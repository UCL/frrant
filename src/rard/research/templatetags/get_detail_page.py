from django import template, urls

register = template.Library()


@register.filter
def get_detail_page(obj):
    page = getattr(obj, "detail_page", None)
    key = getattr(obj, "key", None)
    if key is None or page is None:
        return None
    if page == "topic:detail":
        return urls.reverse(page, kwargs={"slug": key})
    return urls.reverse(page, kwargs={"pk": key})
