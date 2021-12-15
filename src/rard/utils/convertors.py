import re
import string

from django.utils.html import strip_tags

from rard.research.models import AnonymousFragment, Fragment
from rard.research.models.base import FragmentLink


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


def make_plain_text(content):
    no_ufeff = content.replace("\ufeff", "")  # found around mentions for some reason
    # Add a space between tags so adjacent words aren't merged
    no_tags = strip_tags(no_ufeff.replace("><", "> <"))
    no_html_chars = re.sub(r"&\w+;", " ", no_tags)
    no_punctuation = no_html_chars.translate(str.maketrans("", "", string.punctuation))
    no_lone_numbers = re.sub(r"\s\d{1,2}\s", " ", no_punctuation)  # mentions
    no_excess_space = re.sub(r" +", " ", no_lone_numbers)
    return no_excess_space
