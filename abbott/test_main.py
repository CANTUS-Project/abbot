#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/test_main.py
# Purpose:                Tests for __main__.py of the Abbott server.
#
# Copyright (C) 2015 Christopher Antila
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
Tests for ``__main__.py`` of the Abbott server.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

import unittest
from unittest import mock
from tornado import concurrent, httpclient, testing, web
import pysolrtornado
from abbott import __main__ as main


APPLICATION = web.Application(main.HANDLERS)
PORT = testing.bind_unused_port()[1]


def make_future(with_this):
    '''
    Creates a new :class:`Future` with the function's argument as the result.
    '''
    val = concurrent.Future()
    val.set_result(with_this)
    return val


class TestHandler(testing.AsyncHTTPTestCase):
    "Base class for classes that test a ___Handler."
    def get_app(self):
        return APPLICATION

    def get_http_port(self):
        return PORT


class TestAbbott(unittest.TestCase):
    '''
    Tests for module-level things.
    '''

    def get_solr_mock(self):
        '''
        Return a mock Solr object.
        '''
        post = mock.Mock(spec_set=pysolrtornado.Solr)
        # so the async search() method returns 'search results' when yielded
        post.search.return_value = make_future('search results')
        return post

    def test_singular_resource_to_plural_1(self):
        "When the singular form has a corresponding pural."
        self.assertEqual('cantusids', main.singular_resource_to_plural('cantusid'))

    def test_singular_resource_to_plural_2(self):
        "When the singular form doesn't have a corresponding plural."
        self.assertIsNone(main.singular_resource_to_plural('automobiles'))

    @mock.patch('abbott.__main__.SOLR')
    def test_ask_solr_by_id_1(self, mock_solr):
        "Basic test."
        mock_solr = self.get_solr_mock()
        expected = 'search results'
        actual = yield main.ask_solr_by_id('genre', '162')
        self.assertEqual(expected, actual)
        main.SOLR.search.assert_called_once_with('+type:genre +id:162')


class TestSimpleHandler(TestHandler):
    '''
    Tests for the SimpleHandler.
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSimpleHandler, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = main.SimpleHandler(self.get_app(), request, type_name='century')

    def test_initialize_1(self):
        "initialize() works with no extra fields"
        self.assertEqual('century', self.handler.type_name)
        self.assertEqual('centuries', self.handler.type_name_plural)
        self.assertEqual(3, len(self.handler.returned_fields))

    def test_initialize_2(self):
        "initialize() works with extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = main.SimpleHandler(self.get_app(), request, type_name='genre', additional_fields=['mass_or_office'])
        self.assertEqual('genre', actual.type_name)
        self.assertEqual('genres', actual.type_name_plural)
        self.assertEqual(4, len(actual.returned_fields))
        self.assertTrue('mass_or_office' in actual.returned_fields)

    def test_format_record_1(self):
        "basic test"
        input_record = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}
        input_record['false advertising'] = 'not allowed'  # this key obviously should never appear "for real"
        expected = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}
        actual = self.handler.format_record(input_record)
        self.assertEqual(expected, actual)

    def test_make_resource_url_1(self):
        "with no resource_type specified"
        expected = '/centuries/420/'
        actual = self.handler.make_resource_url('420')
        self.assertEqual(expected, actual)

    def test_make_resource_url_2(self):
        "with singuler resource_type"
        expected = '/chants/69/'
        actual = self.handler.make_resource_url('69', 'chant')
        self.assertEqual(expected, actual)

    def test_make_resource_url_3(self):
        "with plural resource_type"
        expected = '/sources/3.14159/'
        actual = self.handler.make_resource_url('3.14159', 'sources')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_1(self, mock_ask_solr):
        "with no resource_id and Solr response has three things"
        resource_id = None
        mock_solr_response = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        expected = {'1': {'id': '1'}, '2': {'id': '2'}, '3': {'id': '3'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = make_future(mock_solr_response)
        self.handler.set_header = mock.Mock()
        self.handler.add_header = mock.Mock()

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*')
        self.assertEqual(expected, actual)
        self.handler.set_header.assert_called_once_with('Server',
                                                        'Abbott/{}'.format(main.ABBOTT_VERSION))
        self.handler.add_header.assert_called_once_with('X-Cantus-Version',
                                                        'Cantus/{}'.format(main.CANTUS_API_VERSION))

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_2(self, mock_ask_solr):
        "with resource_id ending in '/' Solr response is empty"
        resource_id = '123/'
        mock_solr_response = []
        expected = {'resources': {}}
        mock_ask_solr.return_value = make_future(mock_solr_response)
        self.handler.set_header = mock.Mock()
        self.handler.add_header = mock.Mock()

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '123')
        self.assertEqual(expected, actual)
        self.handler.set_header.assert_called_once_with('Server',
                                                        'Abbott/{}'.format(main.ABBOTT_VERSION))
        self.handler.add_header.assert_called_once_with('X-Cantus-Version',
                                                        'Cantus/{}'.format(main.CANTUS_API_VERSION))

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_3(self, mock_ask_solr):
        "with resource_id not ending with '/' and Solr response has one thing"
        resource_id = '888'  # such good luck
        mock_solr_response = [{'id': '888'}]
        expected = {'888': {'id': '888'}, 'resources': {'888': {'self': '/centuries/888/'}}}
        mock_ask_solr.return_value = make_future(mock_solr_response)
        self.handler.set_header = mock.Mock()
        self.handler.add_header = mock.Mock()

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '888')
        self.assertEqual(expected, actual)
        self.handler.set_header.assert_called_once_with('Server',
                                                        'Abbott/{}'.format(main.ABBOTT_VERSION))
        self.handler.add_header.assert_called_once_with('X-Cantus-Version',
                                                        'Cantus/{}'.format(main.CANTUS_API_VERSION))
