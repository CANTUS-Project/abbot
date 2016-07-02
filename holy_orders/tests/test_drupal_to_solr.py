#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_drupal_to_solr.py
# Purpose:                Tests for the "holy_orders.drupal_to_solr" module.
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
Tests for the "holy_orders.drupal_to_solr" module.
'''

# pylint: disable=protected-access
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

import hashlib
import os.path
import pathlib
import tempfile
from unittest import mock
from xml.etree import ElementTree as etree

from  holy_orders import drupal_to_solr


def test_make_solr_id():
    '''
    Ensure the function works. Just run a bunch of things through it.

    It doesn't really matter what the input is, as long as it doesn't change.
    '''
    assert ('2c91c5880c86c969fa1d3585158ed46011424936091116e08e4bdf3e372d9974' ==
        drupal_to_solr.make_solr_id('chant', '444444'))
    assert ('5ba123853a91afeb081b0879d2e676182686370e05fb527009ab17a6e0e715a5' ==
        drupal_to_solr.make_solr_id('source', '79827474'))
    assert ('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' ==
        drupal_to_solr.make_solr_id('', ''))
    assert ('0decd0b369c3b286d2156921509d2ad88b93acffbe1eae1a9fee7951650b963a' ==
        drupal_to_solr.make_solr_id('feast', '162'))


def test_convert_doc_node():
    '''
    Test for convert_doc_node().

    If I make a document that exercises all the  branches, we should be good, right?
    '''
    document = '''
        <chant>
            <image_link>Image</image_link>                                   <!-- this should be ignored -->
            <image_link>https://whatever.com/chants_galore.jpg</image_link>  <!-- this should work -->
            <bologna text="not tasty"/>
            <pancetta>tasty</pancetta>
        </chant>
        '''
    document = etree.fromstring(document)

    actual = drupal_to_solr.convert_doc_node(document)

    assert actual.tag == 'doc'
    kids = list(actual)
    assert len(kids) == 4  # type, image, bologna, pancetta
    assert kids[0].get('name') == 'type'
    assert kids[0].text == 'chant'
    assert kids[1].get('name') == 'image_link'
    assert kids[1].text == 'https://whatever.com/chants_galore.jpg'
    assert kids[2].get('name') == 'bologna'
    assert kids[2].text == 'not tasty'
    assert kids[3].get('name') == 'pancetta'
    assert kids[3].text == 'tasty'


def test_convert_1():
    '''
    Test convert() with a document that has things in it to convert.
    '''
    document = '''
        <chants>
            <chant><a>asdf</a></chant>
            <chant><b>bsdf</b></chant>
        </chants>
        '''
    exp_file = ('''<add><doc><field name="type">chant</field><field name="a">asdf</field></doc>'''
                '''<doc><field name="type">chant</field><field name="b">bsdf</field></doc></add>''')

    actual = drupal_to_solr.convert(document)

    assert isinstance(actual, etree.ElementTree)
    assert exp_file == etree.tostring(actual.getroot(), encoding='unicode')


def test_convert_2():
    '''
    Test convert() with a document that has nothing in it to convert.
    '''
    document = '<chants></chants>'
    exp_file = '<add />'

    actual = drupal_to_solr.convert(document)

    assert isinstance(actual, etree.ElementTree)
    assert exp_file == etree.tostring(actual.getroot(), encoding='unicode')


def test_xreffed_ids():
    '''
    Complex resources, which contain cross-references to other resources in the form of "id" fields,
    must have the cross-referenced IDs modified to match what we will find in Solr.

    In this test, we convert a Feast with Drupal ID 9373, and a Chant that cross-references it. The
    assertion is that the Chant's cross-reference ID should be the same as the Feast's actual ID.

    Regression test for Abbot's GitHub issue #108.
    '''
    feast_xml = etree.fromstring('''
        <feast>
            <id>9373</id>
            <name>Feast of Fun</name>
        </feast>''')
    chant_xml = etree.fromstring('''
        <chant>
            <id>298734</id>
            <feast_id>9373</feast_id>
        </chant>''')

    actual_feast = drupal_to_solr.convert_doc_node(feast_xml)
    actual_chant = drupal_to_solr.convert_doc_node(chant_xml)

    feast_id = actual_feast.find('.//*[@name="id"]')
    xref_id = actual_chant.find('.//*[@name="feast_id"]')
    assert feast_id.text == xref_id.text


class TestFieldConverters(object):
    '''
    Tests for with_inner_text() and with_text_attr().
    '''

    @mock.patch('holy_orders.drupal_to_solr.with_inner_text')
    def test_with_text_attr(self, mock_inner):
        '''
        Just make sure that with_text_attr() works. Quite straightforward.
        '''
        mock_inner.return_value = 5
        elem = etree.Element('asdf', {'text': 'whatever'})

        actual = drupal_to_solr.with_text_attr(elem, 'check it')

        mock_inner.assert_called_with(elem, 'check it')
        assert actual == 5
        assert elem.text == 'whatever'

    def test_with_inner_text_1(self):
        '''
        When it's an "id" field.
        '''
        elem = etree.Element('id')
        elem.text = '162'

        actual = drupal_to_solr.with_inner_text(elem, 'feast')

        assert len(actual) == 1
        actual = actual[0]
        assert actual.tag == 'field'
        assert actual.get('name') == 'id'
        assert actual.text == '0decd0b369c3b286d2156921509d2ad88b93acffbe1eae1a9fee7951650b963a'

    def test_with_inner_text_2(self):
        '''
        When it's a regular old field.
        '''
        elem = etree.Element('ingredient')
        elem.text = 'carrots'

        actual = drupal_to_solr.with_inner_text(elem, 'feast')

        assert len(actual) == 1
        actual = actual[0]
        assert actual.tag == 'field'
        assert actual.get('name') == 'ingredient'
        assert actual.text == 'carrots'

    def test_with_inner_text_3a(self):
        '''
        When it's a "mass_or_office" field, and the value is "Mass."
        '''
        elem = etree.Element('mass_or_office')
        elem.text = 'Mass'

        actual = drupal_to_solr.with_inner_text(elem, 'genre')

        assert len(actual) == 1
        actual = actual[0]
        assert actual.tag == 'field'
        assert actual.get('name') == 'mass_or_office'
        assert actual.text == 'Mass'

    def test_with_inner_text_3b(self):
        '''
        When it's a "mass_or_office" field, and the value is "Office."
        '''
        elem = etree.Element('mass_or_office')
        elem.text = 'Office'

        actual = drupal_to_solr.with_inner_text(elem, 'genre')

        assert len(actual) == 1
        actual = actual[0]
        assert actual.tag == 'field'
        assert actual.get('name') == 'mass_or_office'
        assert actual.text == 'Office'

    def test_with_inner_text_3c(self):
        '''
        When it's a "mass_or_office" field, and the value is "Mass,Office."
        '''
        elem = etree.Element('mass_or_office')
        elem.text = 'Mass,Office'

        actual = drupal_to_solr.with_inner_text(elem, 'genre')

        assert len(actual) == 2
        assert actual[0].tag == 'field'
        assert actual[0].get('name') == 'mass_or_office'
        assert actual[0].text == 'Mass'
        assert actual[1].tag == 'field'
        assert actual[1].get('name') == 'mass_or_office'
        assert actual[1].text == 'Office'

    def test_with_inner_text_4a(self):
        '''
        When it's a field ending with "_id" (and therefore probably a cross-reference).
        '''
        elem = etree.Element('century_id')
        elem.text = '123'

        actual = drupal_to_solr.with_inner_text(elem, 'genre')

        assert len(actual) == 1
        actual = actual[0]
        assert actual.tag == 'field'
        assert actual.get('name') == 'century_id'
        assert actual.text == drupal_to_solr.make_solr_id('century', '123')

    def test_with_inner_text_4b(self):
        '''
        When the whole field is called "_id".
        '''
        elem = etree.Element('_id')
        elem.text = '123'

        actual = drupal_to_solr.with_inner_text(elem, 'genre')

        assert len(actual) == 1
        actual = actual[0]
        assert actual.tag == 'field'
        assert actual.get('name') == '_id'
        assert actual.text == '123'

    def test_with_inner_text_4c(self):
        '''
        When the field is "cantus_id" (so it shouldn't be changed).
        '''
        elem = etree.Element('cantus_id')
        elem.text = '123'

        actual = drupal_to_solr.with_inner_text(elem, 'genre')

        assert len(actual) == 1
        actual = actual[0]
        assert actual.tag == 'field'
        assert actual.get('name') == 'cantus_id'
        assert actual.text == '123'
