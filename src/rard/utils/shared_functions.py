def organise_links(obj):
    """This function will organise links for a fragment/testomonium by grouping the links under their common antiquarian"""
    links = obj.get_all_links()
    organised_links = {}
    is_definite = int

    for link in links:
        antiquarian = link.antiquarian
        if antiquarian in organised_links:
            organised_links[antiquarian].append(link)
        else:
            organised_links[antiquarian] = [link]

    organised_link_array = [
        {antiquarian: [links, is_definite]}
        for antiquarian, links in organised_links.items()
    ]
    return calculate_definite(organised_link_array)


def calculate_definite(organised_link_array):
    """This function determines whether to show the antiquarian as a definite
    link to the fragment/testimonium based on the product of their values"""
    for group in organised_link_array:
        for ant in group.items():
            definite_values = []
            links = ant[1][0]

            for link in links:
                definite_values.append(int(link.definite_antiquarian))
            definite_ant_val = sum(definite_values)
            ant[1][1] = bool(definite_ant_val)
    return organised_link_array


def reassign_to_unknown(worklink):
    """Used in the Remove WorkLink Views"""
    worklink.work = worklink.antiquarian.unknown_work
    worklink.book = worklink.work.unknown_book
    worklink.definite_work = False
    worklink.definite_book = False
    worklink.save()


def collate_unknown(instance):
    """This makes sure there's only one unknown work/book per antiquarian/work and combines contents if otherwise"""
    if instance.__class__.__name__ == "Antiquarian":
        unknown_works = instance.works.filter(unknown=True)
        if unknown_works.count() > 1:
            designated_unknown = unknown_works.first()
            other_unknown_works = unknown_works.exclude(pk=designated_unknown.pk)

            for uw in other_unknown_works:
                transfer_links(instance.fragmentlinks.all(), uw, designated_unknown)
                transfer_links(instance.testimoniumlinks.all(), uw, designated_unknown)
                transfer_links(
                    instance.appositumfragmentlinks.all(), uw, designated_unknown
                )

            other_unknown_works.delete()

    elif instance.__class__.__name__ == "Work":
        unknown_books = instance.book_set.filter(unknown=True)
        if unknown_books.count() > 1:
            designated_unknown = unknown_books.first()
            other_unknown_books = unknown_books.exclude(pk=designated_unknown.pk)

            for ub in other_unknown_books:
                transfer_links(
                    ub.antiquarian_book_fragmentlinks.all(), ub, designated_unknown
                )
                transfer_links(ub.testimoniumlinks.all(), ub, designated_unknown)
                transfer_links(
                    ub.antiquarian_book_appositumfragmentlinks.all(),
                    ub,
                    designated_unknown,
                )

            other_unknown_books.delete()


def transfer_links(links, source_object, target_object):
    for link in links:
        link.work = target_object
        link.save()
