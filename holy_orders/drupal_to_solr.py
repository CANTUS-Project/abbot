#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               holy_orders/drupal_to_solr.py
# Purpose:                Convert Drupal XML to Solr XML.
#
# Copyright (C) 2016 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
'''
Convert Drupal XML to Solr XML.

.. note:: If an element has a @text attribute, that will be used as the text of the outputted
    `<field>` element rather than the text of the input element. It's slightly faster to build the
    input tree using the attribute than the text.

.. note::  If an input element has the "image_link" tag, and its text is "Image," it will not be output.

.. note:: The "solr_unique_id" field is created by this script by combining the "type" field, an
    underscore, and the "id" field. It's because Drupal "id" only has to be unique within a data type.
'''

from collections import defaultdict
import hashlib
from xml.etree import ElementTree as etree


FIELD = 'field'
NAME = 'name'
IMAGE = 'Image'
IMAGE_LINK = 'image_link'
SOLR_UNIQUE_ID = 'solr_unique_id'


def make_solr_id(rtype, rid):
    '''
    Given a resource's "type" and "id" fields from Drupal, determine its "id" field for Solr.

    :param str rtype: The "type" field of a resource.
    :param str rid: The "id" field of a resource.
    :returns: An "id" to use in Solr.
    :rtype: str

    This function exists because Drupal may have more than one resource with the same "id" as long
    as the "type" is different, but CANTUS API resources may not have the same "id" no matter what
    tyep they are.

    The IDs outputted by this function are guaranteed to be consistent for the same type and id.
    '''
    return hashlib.sha256(bytes(rtype + rid, encoding='utf-8')).hexdigest()


def with_text_attr(field, rtype):
    '''
    Convert a Drupal field that has a @text attribute. This is outputted to a single <field> element.

    :param field: A field to convert to Solr XML.
    :type field: :class:`~xml.etree.ElementTree.Element`
    :param str rtype: The type of this resource.
    :returns: An list with :class:`Element` objects to add to the converted document.
    :rtype: list of :class:`~xml.etree.ElementTree.Element`

    The "type" is only used if this is an "id" field.
    '''
    field.text = field.get('text')
    return with_inner_text(field, rtype)


def with_inner_text(field, rtype):
    '''
    Convert a Drupal field that has text between the start and end tags. This is outputted to a
    single <field> element.

    :param field: A field to convert to Solr XML.
    :type field: :class:`~xml.etree.ElementTree.Element`
    :param str rtype: The type of this resource.
    :returns: An list with :class:`Element` objects to add to the converted document.
    :rtype: list of :class:`~xml.etree.ElementTree.Element`

    The "type" is only used if this is an "id" field.
    '''

    elems = [etree.Element(FIELD, {NAME: field.tag.lower()})]

    if field.tag == 'id':
        elems[0].text = make_solr_id(rtype, field.text)

    elif field.tag == 'mass_or_office':
        if field.text in ('Mass', 'Office'):
            elems[0].text = field.text
        else:
            # it's both "Mass" and "Office"
            elems[0].text = 'Mass'
            elems.append(etree.Element(FIELD, {NAME: field.tag.lower()}))
            elems[1].text = 'Office'

    else:
        elems[0].text = field.text

    return elems


def convert_doc_node(document):
    '''
    Convert a single document/resource. This is outputted to a single <doc> element for Solr.
    '''

    out = etree.Element('doc')
    kids = list(document)

    # set node type
    rtype = document.tag
    elem = etree.Element(FIELD, {NAME: 'type'})
    elem.text = document.tag
    out.append(elem)

    # iter them all!
    for each in kids:
        if each.tag == IMAGE_LINK and each.text == IMAGE:
            pass  # skip this element
        elif each.get('text') is not None:
            out.extend(with_text_attr(each, rtype))
        elif each.text is not None:
            out.extend(with_inner_text(each, rtype))

    return out


def convert(input_filename):
    '''
    Convert a Drupal XML file to a Solr XML file.

    :param str input_file: The full pathname of the Drupal XML file to convert.
    :returns: The full pathname of the outputted Solr XML file.
    :rtype: str
    '''
    input_tree = etree.parse(input_filename)
    output_root = etree.Element('add')

    for drupal_node in input_tree.iterfind('*'):
        output_root.append(convert_doc_node(drupal_node))

    if input_filename[-4:] == '.xml':
        output_filename = '{}-out.xml'.format(input_filename[:-4])
    else:
        output_filename = '{}-out.xml'.format(input_filename)

    output_tree = etree.ElementTree(output_root)
    output_tree.write(output_filename, encoding='utf-8', xml_declaration=True)

    return output_filename
