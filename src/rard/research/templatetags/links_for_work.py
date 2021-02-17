from django import template

register = template.Library()


@register.filter
def fragment_links_for_work(antiquarian, work):
    args = {}
    if work:
        args['work'] = work
    else:
        args['work__isnull'] = True

    return antiquarian.fragmentlinks.filter(**args).order_by('work_order')


@register.filter
def testimonium_links_for_work(antiquarian, work):
    args = {}
    if work:
        args['work'] = work
    else:
        args['work__isnull'] = True

    return antiquarian.testimoniumlinks.filter(**args).order_by('work_order')


@register.filter
def appositum_links_for_work(antiquarian, work):
    args = {}
    if work:
        args['work'] = work
    else:
        args['work__isnull'] = True

    return antiquarian.appositumfragmentlinks.filter(
        **args).order_by('work_order')
