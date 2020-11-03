from django import template

register = template.Library()


@register.filter
def has_lock(user, obj):
    return obj.is_locked() and obj.locked_by == user


@register.filter
def lock_request(from_user, obj):
    try:
        return obj.get_object_lock().objectlockrequest_set.filter(
            from_user=from_user
        ).order_by('created').last()
    except AttributeError:
        return None
