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


def transfer_mentions(original, new):
    if original.mentioned_in:
        for tof in original.mentioned_in.all():
            tof.reassign_mentions(
                original, new
            )  # reassign the values in the TOF content from the original to the new object
            tof.update_content_mentions()  # update the mention display text, based on the values set above
            tof.update_mentions()  # updates the relationships on the models based on the above content being updated


# mentions should then just update


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
    fragment_link.definite_antiquarian = appositum_link.definite_antiquarian
    fragment_link.definite_work = appositum_link.definite_work
    fragment_link.definite_book = appositum_link.definite_book
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
    # Transfer apposita
    apposita = fragment.apposita.all()
    anonymous_fragment.anonymous_apposita.add(*apposita)
    # Save new anon fragment and delete fragment
    anonymous_fragment.save()
    reindex_anonymous_fragments()
    transfer_mentions(fragment, anonymous_fragment)
    fragment.delete()
    anonymous_fragment.refresh_from_db()
    return anonymous_fragment


def convert_anonymous_fragment_to_fragment(anonymous_fragment):
    # Only allow for anonymous fragments
    if not isinstance(anonymous_fragment, AnonymousFragment):
        raise FragmentIsNotConvertible

    fragment = Fragment.objects.create()
    transfer_data_between_fragments(anonymous_fragment, fragment)
    transfer_mentions(anonymous_fragment, fragment)
    # If there are AppositumFragmentLinks convert them to FragmentLinks
    for link in anonymous_fragment.appositumfragmentlinks_from.all():
        convert_appositum_link_to_fragment_link(link, fragment)

    # Transfer apposita
    apposita = anonymous_fragment.anonymous_apposita.all()
    fragment.apposita.add(*apposita)

    fragment.save()
    anonymous_fragment.delete()

    return fragment
