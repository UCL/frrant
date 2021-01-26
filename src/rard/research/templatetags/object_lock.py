from django import template

register = template.Library()


@register.filter
def has_lock(user, obj):
    if getattr(obj, 'is_locked', None):
        return obj.is_locked() and obj.locked_by == user
    elif getattr(obj, 'related_lock_object', None):
        # things that are not lockable themselves like original texts
        # but who can be edited if a related object is locked e.g. fragment
        return has_lock(user, obj.related_lock_object())

@register.filter
def lock_request(from_user, obj):
    try:
        return obj.get_object_lock().objectlockrequest_set.filter(
            from_user=from_user
        ).order_by('created').last()
    except AttributeError:
        return None
