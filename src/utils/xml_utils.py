def find_direct_children_with_tag_name(node, name):
    return [child for child in node if child.tag == name]
