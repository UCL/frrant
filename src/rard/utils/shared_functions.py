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


def collate_uw_links(instance, designated_unknown):
    """Used in the collate_unknown functions on Ant/Work models"""
    transfer_links(instance.fragmentlinks.all(), designated_unknown)
    transfer_links(instance.testimoniumlinks.all(), designated_unknown)
    transfer_links(instance.appositumfragmentlinks.all(), designated_unknown)


def collate_ub_links(instance, designated_unknown):
    """Used in the collate_unknown functions on Ant/Work models"""
    instance_type = instance.__class__.__name__
    transfer_links(
        instance.antiquarian_work_fragmentlinks.all(), designated_unknown, instance_type
    )
    transfer_links(
        instance.antiquarian_work_testimoniumlinks.all(),
        designated_unknown,
        instance_type,
    )
    transfer_links(
        instance.antiquarian_work_appositumfragmentlinks.all(),
        designated_unknown,
        instance_type,
    )


def transfer_links(links, target_object, instance_type="Antiquarian"):
    for link in links:
        if instance_type == "Work":
            link.book = target_object
        else:
            link.work = target_object
        link.save()
