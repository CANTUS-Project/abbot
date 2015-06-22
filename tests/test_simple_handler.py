#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_simple_handler.py
# Purpose:                Tests for the Abbott server's SimpleHandler.
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
Tests for the Abbott server's SimpleHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

import copy
from unittest import mock
from tornado import concurrent, escape, httpclient, testing, web
import pysolrtornado
from abbott import __main__ as main
from abbott import handlers, util
import shared


class TestInitialize(shared.TestHandler):
    '''
    Tests for the SimpleHandler.initialize().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestInitialize, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    def test_initialize_1(self):
        "initialize() works with no extra fields"
        self.assertEqual('century', self.handler.type_name)
        self.assertEqual('centuries', self.handler.type_name_plural)
        self.assertEqual(4, len(self.handler.returned_fields))
        self.assertIsNone(self.handler.per_page)
        self.assertIsNone(self.handler.page)

    def test_initialize_2(self):
        "initialize() works with extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'TRue'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = handlers.SimpleHandler(self.get_app(), request, type_name='genre',
                                    additional_fields=['mass_or_office'])
        self.assertEqual('genre', actual.type_name)
        self.assertEqual('genres', actual.type_name_plural)
        self.assertEqual(5, len(actual.returned_fields))
        self.assertTrue('mass_or_office' in actual.returned_fields)
        self.assertTrue(actual.include_resources)

    def test_initialize_3(self):
        "initialize() works with extra fields (different values)"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'fALSe',
                                                  'X-Cantus-Per-Page': '9001',
                                                  'X-Cantus-Page': '3'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = handlers.SimpleHandler(self.get_app(), request, type_name='twist')
        self.assertFalse(actual.include_resources)
        self.assertEqual('9001', actual.per_page)
        self.assertEqual('3', actual.page)


class TestFormatRecord(shared.TestHandler):
    '''
    Tests for the SimpleHandler.format_record().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestFormatRecord, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    def test_format_record_1(self):
        "basic test"
        input_record = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}
        input_record['false advertising'] = 'not allowed'  # this key should never appear "for real"
        expected = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}

        actual = self.handler.format_record(input_record)

        self.assertEqual(expected, actual)
        # ensure fields were counted properly
        self.assertEqual(len(self.handler.returned_fields), len(self.handler.field_counts))
        for field in self.handler.returned_fields:
            self.assertEqual(1, self.handler.field_counts[field])


class TestMakeResourceUrl(shared.TestHandler):
    '''
    Tests for the SimpleHandler.make_resource_url().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestMakeResourceUrl, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

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


class TestBasicGetUnit(shared.TestHandler):
    '''
    Unit tests for the SimpleHandler.basic_get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestBasicGetUnit, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_1(self, mock_ask_solr):
        '''
        - with no resource_id and Solr response has three things
        - self.page is None
        - self.sort is None
        '''
        resource_id = None
        mock_solr_response = shared.make_results([{'id': '1'}, {'id': '2'}, {'id': '3'}])
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=None,
                                              rows=None, sort=None)
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_2(self, mock_ask_solr):
        '''
        - when the id ends with '/' and the Solr response is empty (returns 404)
        '''
        resource_id = '123/'
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.send_error = mock.Mock()
        expected_reason = handlers.SimpleHandler._ID_NOT_FOUND.format('century', resource_id[:-1])

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '123')
        self.assertIsNone(actual)
        self.handler.send_error.assert_called_once_with(404, reason=expected_reason)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_3(self, mock_ask_solr):
        '''
        - with resource_id not ending with '/' and Solr response has one thing
        - self.page is defined but self.per_page isn't
        - self.sort is defined
        '''
        resource_id = '888'  # such good luck
        mock_solr_response = shared.make_results([{'id': '888'}])
        expected = {'888': {'id': '888', 'type': 'century'},
                    'resources': {'888': {'self': '/centuries/888/'}}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.page = 4
        self.handler.sort = 'incipit asc'

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '888')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_4(self, mock_ask_solr):
        '''
        - test_basic_get_unit_1() with self.include_resources set to False
        - self.page and self.per_page are both set
        '''
        resource_id = None
        mock_solr_response = shared.make_results([{'id': '1'}, {'id': '2'}, {'id': '3'}])
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.page = 4
        self.handler.per_page = 12

        self.handler.include_resources = False
        actual = yield self.handler.basic_get(resource_id)

        # "start" should be 36, not 48, because the first "page" is numbered 1, which means a
        # "start" of 0, so "page" 2 should have a "start" equal to "per_page" (12 in this test)
        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=36,
                                              rows=12, sort=None)
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_5(self, mock_ask_solr):
        '''
        - when the Solr response is empty and self.page is too high (returns 400)
        '''
        resource_id = '123'
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.send_error = mock.Mock()
        self.handler.page = 6000

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '123')
        self.assertIsNone(actual)
        self.handler.send_error.assert_called_once_with(400, reason=handlers.SimpleHandler._TOO_LARGE_PAGE)


class TestGetIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestGetIntegration, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_1(self, mock_ask_solr):
        "test_basic_get_unit_1() but through the whole App infrastructure (thus using get())"
        mock_solr_response = shared.make_results([{'id': '1', 'name': 'one'},
                                                  {'id': '2', 'name': 'two'},
                                                  {'id': '3', 'name': 'three'}])
        expected = {'1': {'id': '1', 'name': 'one', 'type': 'century'},
                    '2': {'id': '2', 'name': 'two', 'type': 'century'},
                    '3': {'id': '3', 'name': 'three', 'type': 'century'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        expected_fields = ['id', 'name', 'type']

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET')

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=None,
                                              rows=None, sort=None)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertCountEqual(expected_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_2(self, mock_ask_solr):
        "returns 400 when X-Cantus-Per-Page is set improperly"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': 'force'})

        self.assertEqual(0, mock_ask_solr.call_count)
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(handlers.SimpleHandler._INVALID_PER_PAGE, actual.reason)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_3(self, mock_ask_solr):
        "returns 400 when X-Cantus-Page is set too high"
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '10'})

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=100,
                                              rows=None, sort=None)
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(handlers.SimpleHandler._TOO_LARGE_PAGE, actual.reason)


class TestOptionsIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.options().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    @testing.gen_test
    def test_options_integration_1a(self):
        "ensure the OPTIONS method works as expected ('browse' URL)"
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-Per-Page',
                            'X-Cantus-Page', 'X-Cantus-Sort']
        actual = yield self.http_client.fetch(self.get_url('/genres/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual(handlers.SimpleHandler._ALLOWED_METHODS, actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_options_integration_2a(self, mock_ask_solr):
        "OPTIONS request for non-existent resource gives 404"
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        actual = yield self.http_client.fetch(self.get_url('/genres/nogenre/'),
                                              method='OPTIONS',
                                              raise_error=False)
        self.check_standard_header(actual)
        self.assertEqual(404, actual.code)
        mock_ask_solr.assert_called_once_with('genre', 'nogenre')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_options_integration_2b(self, mock_ask_solr):
        "OPTIONS request for existing resource returns properly ('view' URL)"
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields']
        mock_solr_response = shared.make_results(['Versicle'])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        actual = yield self.http_client.fetch(self.get_url('/genres/162/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual(0, len(actual.body))
        mock_ask_solr.assert_called_once_with('genre', '162')
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())


class TestHeadIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.head().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestHeadIntegration, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_head_integration_1a(self, mock_ask_solr):
        "test_get_integration_1() but with the HEAD method"
        mock_solr_response = shared.make_results([{'id': '1'}, {'id': '2'}, {'id': '3'}])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='HEAD')

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=None,
                                              rows=None, sort=None)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertEqual(0, len(actual.body))
