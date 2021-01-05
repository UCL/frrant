from django import template

register = template.Library()


@register.filter
def fragment_links_for_work(obj, work):
    return obj.fragmentlinks.filter(work=work).order_by('work_order')


@register.filter
def testimonium_links_for_work(obj, work):
    return obj.testimoniumlinks.filter(work=work).order_by('work_order')
