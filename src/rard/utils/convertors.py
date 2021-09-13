from rard.research.models import AnonymousFragment

class FragmentIsNotConvertible(Exception):
    """
    Only unlinked fragments can be converted to anonymous fragments
    """
    pass

def convert_unlinked_to_anonymous(fragment):

    # Only allow for unlinked fragments
    if not fragment.is_unlinked:
        raise FragmentIsNotConvertible
    
    anonymous_fragment = AnonymousFragment.objects.create()

    # Directly assigned fields
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

    # Save changes
    anonymous_fragment.save()

    # finally, delete the fragment
    fragment.delete()

    return anonymous_fragment
