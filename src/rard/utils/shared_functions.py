def organise_links(obj):
    links = obj.get_all_links()
    organised_links = {}

    for link in links:
        antiquarian = link.antiquarian
        print(link.definite_antiquarian)
        if antiquarian in organised_links:
            organised_links[antiquarian].append(link)
        else:
            organised_links[antiquarian] = [link]

    organised_link_array = [
        {antiquarian: links} for antiquarian, links in organised_links.items()
    ]
    return organised_link_array
