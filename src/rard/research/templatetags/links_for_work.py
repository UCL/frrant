from django import template

register = template.Library()


@register.filter
def testimonium_links_for_work(antiquarian, work):
    args = {}
    if work:
        args["work"] = work
    else:
        args["work__isnull"] = True

    return antiquarian.testimoniumlinks.filter(**args).order_by("work_order")


@register.filter
def fragment_links_by_work(antiquarian):
    return get_links_by_work(antiquarian.fragmentlinks, "fragment")


@register.filter
def testimonium_links_by_work(antiquarian):
    return get_links_by_work(antiquarian.testimoniumlinks, "testimonium")


@register.filter
def appositum_links_by_work(antiquarian):
    return get_links_by_work(antiquarian.appositumfragmentlinks, "anonymous_fragment")


def get_links_by_work(links, related):
    work_to_object = {}
    for obj in links.order_by("work_order").select_related(related):
        w = obj.work_id
        if w not in work_to_object:
            work_to_object[w] = []
        work_to_object[w].append(obj)
    return work_to_object
