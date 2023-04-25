from rard.research.models import AnonymousFragment, Fragment
from rard.research.models.base import FragmentLink
from rard.research.models.fragment import reindex_anonymous_fragments


class FragmentIsNotConvertible(Exception):
    """
    Only unlinked fragments and anonymous fragments can be converted
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


def convert_appositum_link_to_fragment_link(appositum_link, fragment):
    """
    Creates a new FragmentLink based on the AppositumFragmentLink data and
    links it to the fragment provided.
    Ignores the following AppositumFragmentLink fields:
    - linked_to
    - exclusive
    - link_object
    """
    fragment_link = FragmentLink.objects.create(fragment=fragment)
    fragment_link.antiquarian = appositum_link.antiquarian
    fragment_link.order = appositum_link.order
    fragment_link.definite = appositum_link.definite
    fragment_link.work = appositum_link.work
    fragment_link.work_order = appositum_link.work_order
    fragment_link.book = appositum_link.book
    fragment_link.save()
    return fragment_link


def convert_unlinked_fragment_to_anonymous_fragment(fragment):
    # Only allow for unlinked fragments
    if not fragment.is_unlinked:
        raise FragmentIsNotConvertible

    anonymous_fragment = AnonymousFragment.objects.create()
    transfer_data_between_fragments(fragment, anonymous_fragment)
    anonymous_fragment.save()
    fragment.delete()
    reindex_anonymous_fragments()
    anonymous_fragment.refresh_from_db()
    return anonymous_fragment


def convert_anonymous_fragment_to_fragment(anonymous_fragment):
    # Only allow for anonymous fragments
    if not isinstance(anonymous_fragment, AnonymousFragment):
        raise FragmentIsNotConvertible

    fragment = Fragment.objects.create()
    transfer_data_between_fragments(anonymous_fragment, fragment)

    # If there are AppositumFragmentLinks convert them to FragmentLinks
    for link in anonymous_fragment.appositumfragmentlinks_from.all():
        convert_appositum_link_to_fragment_link(link, fragment)

    fragment.save()
    anonymous_fragment.delete()

    return fragment
