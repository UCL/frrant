import math


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

            definite_ant_val = math.prod(definite_values)
            ant[1][1] = bool(definite_ant_val)
    return organised_link_array
