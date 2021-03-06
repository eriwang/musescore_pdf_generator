import xml.etree.ElementTree as ET


def find_exactly_one(node, find_arg):
    children = node.findall(find_arg)
    num_children = len(children)
    if num_children != 1:
        raise ValueError(f'Found {num_children} children in node {node.tag} find_arg {find_arg}, expected 1')

    return children[0]


def create_node_with_text(tag, text):
    element = ET.Element(tag)
    element.text = text
    return element
