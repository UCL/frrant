from rard.research.models import AnonymousFragment, Fragment


class FragmentIsNotConvertible(Exception):
    """
    Conversion is only possible between unlinked fragments and anonymous fragments
    """

    pass


def transfer_data_between_fragments(source, destination):
    # Directly assigned fields
    destination.name = source.name
    destination.date_range = source.date_range
    destination.collection_id = source.collection_id
    destination.order_year = source.order_year

    # Fields requiring set method
    destination.topics.set(source.topics.all())
    destination.images.set(source.images.all())
    # source is no longer the owner after this:
    destination.original_texts.set(source.original_texts.all())

    # Need to remove commentary's original relationship with source or
    # it will be deleted when we delete the source
    commentary = source.commentary
    source.commentary = None
    destination.commentary = commentary


def convert_unlinked_to_anonymous(fragment):

    # Only allow for unlinked fragments
    if not fragment.is_unlinked:
        raise FragmentIsNotConvertible

    anonymous_fragment = AnonymousFragment.objects.create()
    transfer_data_between_fragments(fragment, anonymous_fragment)
    anonymous_fragment.save()
    fragment.delete()

    return anonymous_fragment


def convert_anonymous_to_unlinked(anonymous_fragment):

    # Only allow for anonymous fragments
    if not isinstance(anonymous_fragment, AnonymousFragment):
        raise FragmentIsNotConvertible

    fragment = Fragment.objects.create()
    transfer_data_between_fragments(anonymous_fragment, fragment)
    fragment.save()
    anonymous_fragment.delete()

    return fragment
