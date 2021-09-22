from rard.research.models import AnonymousFragment, Fragment


class FragmentIsNotConvertible(Exception):
    """
    Conversion is only possible between unlinked fragments and anonymous fragments
    """

    pass


def convert_unlinked_to_anonymous(fragment):

    # Only allow for unlinked fragments
    if not fragment.is_unlinked:
        raise FragmentIsNotConvertible

    anonymous_fragment = AnonymousFragment.objects.create()

    # Directly assigned fields
    anonymous_fragment.name = fragment.name
    anonymous_fragment.date_range = fragment.date_range
    anonymous_fragment.collection_id = fragment.collection_id
    anonymous_fragment.order_year = fragment.order_year

    # Fields requiring set method
    anonymous_fragment.topics.set(fragment.topics.all())
    anonymous_fragment.images.set(fragment.images.all())
    # fragment is no longer the owner after this:
    anonymous_fragment.original_texts.set(fragment.original_texts.all())

    # Need to remove commentary's original relationship with fragment or
    # it will be deleted when we delete the fragment
    commentary = fragment.commentary
    fragment.commentary = None
    anonymous_fragment.commentary = commentary

    # Save changes and delete the fragment
    anonymous_fragment.save()
    fragment.delete()

    return anonymous_fragment


def convert_anonymous_to_unlinked(anonymous_fragment):

    # Only allow for anonymous fragments
    if not isinstance(anonymous_fragment, AnonymousFragment):
        raise FragmentIsNotConvertible

    fragment = Fragment.objects.create()

    # Directly assigned fields
    fragment.name = anonymous_fragment.name
    fragment.date_range = anonymous_fragment.date_range
    fragment.collection_id = anonymous_fragment.collection_id
    fragment.order_year = anonymous_fragment.order_year

    # Fields requiring set method
    fragment.topics.set(anonymous_fragment.topics.all())
    fragment.images.set(anonymous_fragment.images.all())

    # anonymous_fragment is no longer the owner after this:
    fragment.original_texts.set(anonymous_fragment.original_texts.all())

    # Need to remove commentary's original relationship with fragment or
    # it will be deleted when we delete the fragment
    commentary = anonymous_fragment.commentary
    anonymous_fragment.commentary = None
    fragment.commentary = commentary

    # Save changes and delete the anonymous fragment
    fragment.save()
    anonymous_fragment.delete()

    return fragment
