#!/usr/bin/env python3

DEBUG = False

# Convert an XML export from the CANTUS Drupal database into Solr XML
#
# Exported Taxonomy Terms:
# - genres
# - feasts
# - centuries
# - notations
# - offices
# - portfolia (not used anywhere?)
# - provenances
# - segments
# - source statii
#
# Exported Resources:
# - indexers
# - chants
# - sources
#
# NOTE: "CantusID" records require using the "chants_to_cantusids.py" script
#
# NOTE:
# If an element has a @text attribute, that will be used as the text of the outputted <field>
#    element rather than the text of the input element. It's slightly faster to build the input
#    tree using the attribute than the text.
#
# NOTE:
# If an input element has the "image_link" tag, and its text is "Image," it will not be output.

from collections import defaultdict
import sys
from xml.etree import ElementTree as ETree


FIELD = 'field'
NAME = 'name'
IMAGE = 'Image'
IMAGE_LINK = 'image_link'


def solr_node_from_drupal_node(node):
    '''
    '''
    out = ETree.Element('doc')
    kids = list(node)

    # set node type
    elem = ETree.Element(FIELD, {NAME: 'type'})
    elem.text = node.tag
    out.append(elem)

    # iter them all!
    for each in kids:
        if each.tag == IMAGE_LINK and each.text == IMAGE:
            pass  # skip this element
        elif each.get('text') is not None:
            elem = ETree.Element(FIELD, {NAME: each.tag.lower()})
            elem.text = each.get('text')
            out.append(elem)
        elif each.text is not None:
            elem = ETree.Element(FIELD, {NAME: each.tag.lower()})
            elem.text = each.text
            out.append(elem)

    return out


def make_new_filename(old_filename):
    '''
    '''
    if old_filename[-4:] == '.xml':
        return '{}-out.xml'.format(old_filename[:-4])
    else:
        return '{}-out.xml'.format(old_filename)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        if 'python' in sys.argv[0]:
            print('Usage: python3 drupal_xml_to_solr_xml.py *filename*')
            print('')
            print('Convert an XML export from the CANTUS Drupal database into Solr XML.')
            raise SystemExit()
        else:
            filename = sys.argv[1]
    else:
        filename = sys.argv[2]

    input_tree = ETree.parse(filename)
    output_root = ETree.Element('add')

    for drupal_node in input_tree.iterfind('*'):
        output_root.append(solr_node_from_drupal_node(drupal_node))

    output_filename = make_new_filename(filename)
    if DEBUG:
        output_me = '\n'.join(ETree.tostringlist(output_root, encoding='unicode'))
        with open(output_filename, 'w') as the_file:
            written = the_file.write(output_me)
        if written < len(output_me):
            print('Error: unable to write full file to "{}"'.format(output_filename))
            raise SystemExit(1)
    else:
        output_tree = ETree.ElementTree(output_root)
        output_tree.write(output_filename, encoding='utf-8', xml_declaration=True)

    print('Info: results outputted to "{}"'.format(output_filename))
