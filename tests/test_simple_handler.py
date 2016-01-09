#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_simple_handler.py
# Purpose:                Tests for the Abbot server's SimpleHandler.
#
# Copyright (C) 2015, 2016 Christopher Antila
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
Tests for the Abbot server's SimpleHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock
from tornado import escape, httpclient, testing
import pysolrtornado
from abbot import __main__ as main
from abbot.complex_handler import ComplexHandler
from abbot import simple_handler
from abbot import util
SimpleHandler = simple_handler.SimpleHandler
import shared


class TestInitialize(shared.TestHandler):
    '''
    Tests for the SimpleHandler.initialize().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def test_initialize_1(self):
        "initialize() works with no extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='century')
        self.assertEqual('century', actual.type_name)
        self.assertEqual('centuries', actual.type_name_plural)
        self.assertEqual(4, len(actual.returned_fields))
        self.assertIsNone(actual.hparams['per_page'])
        self.assertIsNone(actual.hparams['page'])

    def test_initialize_2(self):
        "initialize() works with extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'TRue'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='genre',
                               additional_fields=['mass_or_office'])
        self.assertEqual('genre', actual.type_name)
        self.assertEqual('genres', actual.type_name_plural)
        self.assertEqual(5, len(actual.returned_fields))
        self.assertTrue('mass_or_office' in actual.returned_fields)
        self.assertTrue(actual.hparams['include_resources'])

    def test_initialize_3(self):
        "initialize() works with extra fields (different values)"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-No-Xref': 'code yellow',
                                                  'X-Cantus-Fields': 'code black'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='twist')
        self.assertEqual('code red', actual.hparams['include_resources'])
        self.assertEqual('code blue', actual.hparams['per_page'])
        self.assertEqual('code green', actual.hparams['page'])
        self.assertEqual('code white', actual.hparams['sort'])
        self.assertEqual('code yellow', actual.hparams['no_xref'])
        self.assertEqual('code black', actual.hparams['fields'])

    def test_initialize_4(self):
        "initialize() works with SEARCH request (no values set in request body)"
        request = httpclient.HTTPRequest(url='/zool/', method='SEARCH',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-No-Xref': 'code yellow',
                                                  'X-Cantus-Fields': 'code black'},
                                         body='{}')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='twist')
        self.assertEqual('code red', actual.hparams['include_resources'])
        self.assertEqual('code blue', actual.hparams['per_page'])
        self.assertEqual('code green', actual.hparams['page'])
        self.assertEqual('code white', actual.hparams['sort'])
        self.assertEqual('code yellow', actual.hparams['no_xref'])
        self.assertEqual('code black', actual.hparams['fields'])

    def test_initialize_5(self):
        "initialize() works with SEARCH request (all values set in request body)"
        request = httpclient.HTTPRequest(url='/zool/', method='SEARCH',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-No-Xref': 'code yellow',
                                                  'X-Cantus-Fields': 'code black'},
                                         body='{"include_resources": "red code",'
                                               '"per_page": "blue code",'
                                               '"page": "green code",'
                                               '"sort": "white code",'
                                               '"no_xref": "yellow code",'
                                               '"fields": "black code",'
                                               '"query": "whatever"}')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='twist')
        self.assertEqual('red code', actual.hparams['include_resources'])
        self.assertEqual('blue code', actual.hparams['per_page'])
        self.assertEqual('green code', actual.hparams['page'])
        self.assertEqual('white code', actual.hparams['sort'])
        self.assertEqual('yellow code', actual.hparams['no_xref'])
        self.assertEqual('black code', actual.hparams['fields'])
        self.assertEqual('whatever', actual.hparams['search_query'])

    @mock.patch('abbot.simple_handler.SimpleHandler.send_error')
    def test_initialize_6(self, mock_send_error):
        "initialize() works with SEARCH request (JSON is faulty)"
        request = httpclient.HTTPRequest(url='/zool/', method='SEARCH',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-No-Xref': 'code yellow',
                                                  'X-Cantus-Fields': 'code black'},
                                         body='{include_resources: "red code"}')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='twist')
        self.assertIsNone(actual.hparams['search_query'])
        mock_send_error.assert_called_once_with(400, reason=simple_handler._MISSING_SEARCH_BODY)

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
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')

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
    Tests for the SimpleHandler.make_resource_url() and SimpleHandler.make_drupal_url().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestMakeResourceUrl, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')

    def test_make_resource_url_1(self):
        "with no resource_type specified"
        expected = 'https://cantus.org/centuries/420/'
        actual = self.handler.make_resource_url('420')
        self.assertEqual(expected, actual)

    def test_make_resource_url_2(self):
        "with singuler resource_type"
        expected = 'https://cantus.org/chants/69/'
        actual = self.handler.make_resource_url('69', 'chant')
        self.assertEqual(expected, actual)

    def test_make_resource_url_3(self):
        "with plural resource_type"
        expected = 'https://cantus.org/sources/3.14159/'
        actual = self.handler.make_resource_url('3.14159', 'sources')
        self.assertEqual(expected, actual)

    def test_make_drupal_url_1(self):
        "options.drupal_path is None"
        expected = ''
        res_id = '123'
        res_type = None
        simple_handler.options.drupal_url = None
        simple_handler.options.drupal_type_map = {}
        actual = self.handler.make_drupal_url(res_id, res_type)
        self.assertEqual(expected, actual)

    def test_make_drupal_url_2(self):
        "res_type is None; it's also mapped to None"
        expected = ''
        res_id = '123'
        res_type = None
        simple_handler.options.drupal_url = 'asdf'
        simple_handler.options.drupal_type_map = {'century': None}
        actual = self.handler.make_drupal_url(res_id, res_type)
        self.assertEqual(expected, actual)

    def test_make_drupal_url_3(self):
        "res_type is something; it's mapped to something; drupal_url ends with a /"
        expected = 'asdf/boop/123'
        res_id = '123'
        res_type = 'beep'
        simple_handler.options.drupal_url = 'asdf/'
        simple_handler.options.drupal_type_map = {'beep': 'boop'}
        actual = self.handler.make_drupal_url(res_id, res_type)
        self.assertEqual(expected, actual)

    def test_make_drupal_url_4(self):
        "res_type isn't in the mapping"
        expected = 'asdf/century/123'
        res_id = '123'
        res_type = None
        simple_handler.options.drupal_url = 'asdf'
        simple_handler.options.drupal_type_map = {}
        actual = self.handler.make_drupal_url(res_id, res_type)
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
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_basic_get_unit_1(self):
        '''
        - with no resource_id and Solr response has three things
        - self.hparams['page'] is 1 (default)
        - self.hparams['sort'] is None
        - options.drupal_url is 'http://drp'
        '''
        simple_handler.options.drupal_url = 'http://drp'
        resource_id = None
        self.handler.hparams['page'] = 1
        self.handler.hparams['per_page'] = 10
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '3', 'name': 'three', 'type': 'century'})
        expected = {'1': {'id': '1', 'name': 'one', 'type': 'century', 'drupal_path': 'http://drp/century/1'},
                    '2': {'id': '2', 'name': 'two', 'type': 'century', 'drupal_path': 'http://drp/century/2'},
                    '3': {'id': '3', 'name': 'three', 'type': 'century', 'drupal_path': 'http://drp/century/3'},
                    'resources': {'1': {'self': 'https://cantus.org/centuries/1/'},
                                  '2': {'self': 'https://cantus.org/centuries/2/'},
                                  '3': {'self': 'https://cantus.org/centuries/3/'}},
                    'sort_order': ['1', '2', '3'],
        }
        exp_num = 3

        actual = yield self.handler.basic_get(resource_id)

        self.solr.search.asset_called_with('+type:century +id:*', start=0, df='default_search')
        assert (expected, exp_num) == actual

    @testing.gen_test
    def test_basic_get_unit_2(self):
        '''
        - when the id ends with '/' and the Solr response is empty (returns 404)
        - it's a browse request, so "page" and "per_page" are None
        '''
        resource_id = '123/'
        self.handler.hparams['page'] = None
        self.handler.hparams['per_page'] = None
        self.handler.send_error = mock.Mock()
        expected_reason = simple_handler._ID_NOT_FOUND.format('century', resource_id[:-1])

        actual = yield self.handler.basic_get(resource_id)

        self.solr.search.assert_called_with('+type:century +id:123', df='default_search')
        self.handler.send_error.assert_called_once_with(404, reason=expected_reason)
        assert (None, 0) == actual

    @testing.gen_test
    def test_basic_get_unit_3(self):
        '''
        - with resource_id not ending with '/' and Solr response has one thing
        - self.hparams['page'] is not default but self.handler.hparams['per_page'] is
        - self.hparams['sort'] is defined
        - options.drupal_url is defined
        '''
        resource_id = '888'  # such good luck
        self.solr.search_se.add('888', {'id': '888', 'type': 'century'})
        expected = {'888': {'id': '888', 'type': 'century'},
                    'resources': {'888': {'self': 'https://cantus.org/centuries/888/'}},
                    'sort_order': ['888'],
        }
        self.handler.hparams['page'] = 42
        self.handler.hparams['per_page'] = 10
        self.handler.hparams['sort'] = 'incipit asc'
        exp_num = 1

        actual = yield self.handler.basic_get(resource_id)

        self.solr.search.assert_called_with('+type:century +id:888', df='default_search')
        assert (expected, exp_num) == actual

    @testing.gen_test
    def test_basic_get_unit_4(self):
        '''
        - test_basic_get_unit_1() with self.hparams['include_resources'] set to False
        - self.hparams['page'] and self.handler.hparams['per_page'] are both set
        '''
        resource_id = None
        self.solr.search_se.add('*', {'id': '1', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '3', 'type': 'century'})
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'}, 'sort_order': ['1', '2', '3']}
        self.handler.hparams['page'] = 4
        self.handler.hparams['per_page'] = 12
        self.handler.hparams['include_resources'] = False
        exp_num = 3

        actual  = yield self.handler.basic_get(resource_id)

        # "start" should be 36, not 48, because the first "page" is numbered 1, which means a
        # "start" of 0, so "page" 2 should have a "start" equal to "per_page" (12 in this test)
        self.solr.search.assert_called_with('+type:century +id:*', start=36, rows=12, df='default_search')
        assert (expected, exp_num) == actual

    @testing.gen_test
    def test_basic_get_unit_5(self):
        '''
        - when the Solr response is empty and self.hparams['page'] is too high (returns 409)
        '''
        resource_id = '123'
        self.handler.hparams['page'] = 1
        self.handler.hparams['per_page'] = 10
        self.handler.send_error = mock.Mock()
        self.handler.hparams['page'] = 6000
        exp_reason = simple_handler._TOO_LARGE_PAGE

        actual = yield self.handler.basic_get(resource_id)

        self.solr.search.assert_called_with('+type:century +id:123', df='default_search')
        self.handler.send_error.assert_called_once_with(409, reason=exp_reason)
        assert (None, 0) == actual

    @testing.gen_test
    def test_basic_get_unit_6(self):
        '''
        - when a SEARCH query yields no results (returns 404)
        '''
        query = 'find me this'
        self.handler.hparams['page'] = 1
        self.handler.hparams['per_page'] = 10
        self.handler.send_error = mock.Mock()
        expected_reason = simple_handler._NO_SEARCH_RESULTS

        actual = yield self.handler.basic_get(query=query)

        # NOTE: shouldn't the query be '+type:century {}'.format(query) ??? No! Because the "type"
        #       part is added by search_handler(), not by basic_get().
        self.solr.search.assert_called_with(query, df='default_search', rows=10)
        self.handler.send_error.assert_called_once_with(404, reason=expected_reason)
        assert (None, 0) == actual

    @testing.gen_test
    def test_basic_get_unit_7(self):
        '''
        Inherited from test_basic_get_unit_1():
        - with no resource_id and Solr response has three things
        - self.hparams['page'] is 1 (default)
        - self.hparams['sort'] is None
        - options.drupal_url is 'http://drp'

        New in this test:
        - the things returned from Solr are three different types
        '''
        simple_handler.options.drupal_url = 'http://drp'
        resource_id = None
        self.handler.hparams['page'] = 1
        self.handler.hparams['per_page'] = 10
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'feast'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'genre'})
        self.solr.search_se.add('*', {'id': '3', 'name': 'three', 'type': 'source'})
        expected = {'1': {'id': '1', 'name': 'one', 'type': 'feast', 'drupal_path': 'http://drp/feast/1'},
                    '2': {'id': '2', 'name': 'two', 'type': 'genre', 'drupal_path': 'http://drp/genre/2'},
                    '3': {'id': '3', 'name': 'three', 'type': 'source', 'drupal_path': 'http://drp/source/3'},
                    'resources': {'1': {'self': 'https://cantus.org/feasts/1/'},
                                  '2': {'self': 'https://cantus.org/genres/2/'},
                                  '3': {'self': 'https://cantus.org/sources/3/'}},
                    'sort_order': ['1', '2', '3'],
        }
        exp_num = 3

        actual = yield self.handler.basic_get(resource_id)

        self.solr.search.assert_called_with('+type:century +id:*', rows=10, df='default_search')
        assert (expected, exp_num) == actual

    @testing.gen_test
    def test_basic_get_unit_8(self):
        '''
        - when a GET request has an invalid resource ID
        NOTE: didn't set up Solr mock
        '''
        resource_id = '-888_'
        self.handler.send_error = mock.Mock()
        expected_reason = simple_handler._INVALID_ID

        actual = yield self.handler.basic_get(resource_id)

        self.handler.send_error.assert_called_once_with(422, reason=expected_reason)
        assert (None, 0) == actual


class TestGetUnit(shared.TestHandler):
    '''
    Unit tests for the SimpleHandler.get() and SimpleHandler.get_handler().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestGetUnit, self).setUp()
        self.request = httpclient.HTTPRequest(url='/zool/', method='GET')
        self.request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), self.request, type_name='century')

    def test_normal_browse(self):
        '''
        Preconditions:
        - resource_id is None
        - self.hparams['include_resources'] is True
        - self.verify_request_headers() returns True
        - self.get_handler() returns Future with three-item list
        - self.head_request is False

        Postconditions:
        - is_browse_request is True
        - self.verify_request_headers() called with True
        - self.get_handler() called with None
        - self.make_response_headers() called with (True, 2)
        - self.write() is called
        '''
        resource_id = None
        self.handler.hparams['include_resources'] = True
        self.handler.head_request = False
        mock_vrh = mock.Mock(return_value=True)
        self.handler.verify_request_headers = mock_vrh
        response = ([1, 2, 3], 1900)
        mock_get_handler = mock.Mock(return_value=shared.make_future(response))
        self.handler.get_handler = mock_get_handler
        mock_mrh = mock.Mock()
        self.handler.make_response_headers = mock_mrh
        mock_write = mock.Mock()
        self.handler.write = mock_write

        self.handler.get(resource_id)

        mock_vrh.assert_called_once_with(True)
        mock_get_handler.assert_called_once_with(resource_id)
        mock_mrh.assert_called_once_with(True, response[1])
        mock_write.assert_called_once_with(response[0])

    def test_normal_view(self):
        '''
        Preconditions:
        - resource_id is '123'
        - self.hparams['include_resources'] is False
        - self.verify_request_headers() returns True
        - self.get_handler() returns Future with one-item list
        - self.head_request is True

        Postconditions:
        - is_browse_request is False
        - self.verify_request_headers() called with False
        - self.get_handler() called with '123'
        - self.make_response_headers() called with (False, 1)
        - self.write() is not called
        '''
        resource_id = '123'
        self.handler.hparams['include_resources'] = False
        self.handler.head_request = True
        mock_vrh = mock.Mock(return_value=True)
        self.handler.verify_request_headers = mock_vrh
        response = ([1], 42)
        mock_get_handler = mock.Mock(return_value=shared.make_future(response))
        self.handler.get_handler = mock_get_handler
        mock_mrh = mock.Mock()
        self.handler.make_response_headers = mock_mrh
        mock_write = mock.Mock()
        self.handler.write = mock_write

        self.handler.get(resource_id)

        mock_vrh.assert_called_once_with(False)
        mock_get_handler.assert_called_once_with(resource_id)
        mock_mrh.assert_called_once_with(False, response[1])
        self.assertEqual(0, mock_write.call_count)

    def test_no_resources_found(self):
        '''
        Preconditions:
        - resource_id is None
        - self.verify_request_headers() returns True
        - self.get_handler() returns Future with None
        - self.head_request is False

        Postconditions:
        - is_browse_request is True
        - self.verify_request_headers() called with True
        - self.get_handler() called with None
        - self.make_response_headers() is not called
        - self.write() is not called
        '''
        resource_id = None
        self.handler.hparams['include_resources'] = True
        self.handler.head_request = False
        mock_vrh = mock.Mock(return_value=True)
        self.handler.verify_request_headers = mock_vrh
        response = (None , 0)
        mock_get_handler = mock.Mock(return_value=shared.make_future(response))
        self.handler.get_handler = mock_get_handler
        mock_mrh = mock.Mock()
        self.handler.make_response_headers = mock_mrh
        mock_write = mock.Mock()
        self.handler.write = mock_write

        self.handler.get(resource_id)

        mock_vrh.assert_called_once_with(True)
        mock_get_handler.assert_called_once_with(resource_id)
        self.assertEqual(0, mock_mrh.call_count)
        self.assertEqual(0, mock_write.call_count)

    def test_bad_headers(self):
        '''
        Preconditions:
        - resource_id is None
        - self.verify_request_headers() returns False
        - self.head_request is False

        Postconditions:
        - is_browse_request is True
        - self.verify_request_headers() called with True
        - self.get_handler() is not called
        - self.make_response_headers() is not called
        - self.write() is not called
        '''
        resource_id = None
        self.handler.hparams['include_resources'] = True
        self.handler.head_request = False
        mock_vrh = mock.Mock(return_value=False)
        self.handler.verify_request_headers = mock_vrh
        response = None
        mock_get_handler = mock.Mock(return_value=shared.make_future(response))
        self.handler.get_handler = mock_get_handler
        mock_mrh = mock.Mock()
        self.handler.make_response_headers = mock_mrh
        mock_write = mock.Mock()
        self.handler.write = mock_write

        self.handler.get(resource_id)

        mock_vrh.assert_called_once_with(True)
        self.assertEqual(0, mock_get_handler.call_count)
        self.assertEqual(0, mock_mrh.call_count)
        self.assertEqual(0, mock_write.call_count)

    def test_solr_error(self):
        '''
        Preconditions:
        - resource_id is None
        - self.verify_request_headers() returns True
        - self.get_handler() raises pysolrtornado.SolrError
        - self.head_request is False

        Postconditions:
        - is_browse_request is True
        - self.verify_request_headers() called with True
        - self.get_handler() called with None
        - self.make_response_headers() is not called
        - self.write() is not called
        - self.send_error() is called with (502, reason=SimpleHandler._SOLR_502_ERROR)
        '''
        resource_id = None
        self.handler.hparams['include_resources'] = True
        self.handler.head_request = False
        mock_vrh = mock.Mock(return_value=True)
        self.handler.verify_request_headers = mock_vrh
        mock_get_handler = mock.Mock(side_effect=pysolrtornado.SolrError)
        self.handler.get_handler = mock_get_handler
        mock_mrh = mock.Mock()
        self.handler.make_response_headers = mock_mrh
        mock_write = mock.Mock()
        self.handler.write = mock_write
        mock_send_error = mock.Mock()
        self.handler.send_error = mock_send_error

        self.handler.get(resource_id)

        mock_vrh.assert_called_once_with(True)
        mock_get_handler.assert_called_once_with(resource_id)
        self.assertEqual(0, mock_mrh.call_count)
        self.assertEqual(0, mock_write.call_count)
        mock_send_error.assert_called_once_with(502, reason=simple_handler._SOLR_502_ERROR)

    @mock.patch('abbot.simple_handler.SimpleHandler.basic_get')
    @testing.gen_test
    def test_get_handler_1(self, mock_basic_get):
        '''
        Ensure the kwargs are passed along properly.
        '''
        mock_basic_get.return_value = shared.make_future('five')
        resource_id = '123'
        query = 'i can haz cheezburger?'
        actual = yield self.handler.get_handler(resource_id=resource_id, query=query)
        self.assertEqual('five', actual)
        mock_basic_get.assert_called_once_with(resource_id=resource_id, query=query)


class TestGetIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestGetIntegration, self).setUp()
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_get_integration_1(self):
        "test_basic_get_unit_1() but through the whole App infrastructure (thus using get())"
        simple_handler.options.drupal_url = 'http://drp'
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '3', 'name': 'three', 'type': 'century'})
        expected = {'1': {'id': '1', 'name': 'one', 'type': 'century', 'drupal_path': 'http://drp/century/1'},
                    '2': {'id': '2', 'name': 'two', 'type': 'century', 'drupal_path': 'http://drp/century/2'},
                    '3': {'id': '3', 'name': 'three', 'type': 'century', 'drupal_path': 'http://drp/century/3'},
                    'resources': {'1': {'self': 'https://cantus.org/centuries/1/'},
                                  '2': {'self': 'https://cantus.org/centuries/2/'},
                                  '3': {'self': 'https://cantus.org/centuries/3/'}},
                    'sort_order': ['1', '2', '3'],
        }
        expected_fields = ['id', 'name', 'type']

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET')

        self.solr.search.assert_called_once_with('+type:century +id:*', df='default_search', rows=10)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertCountEqual(expected_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_get_integration_2(self):
        "returns 400 when X-Cantus-Per-Page is set improperly"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': 'force'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_get_integration_3(self):
        "returns 400 when X-Cantus-Page is set too high"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '10'})

        self.solr.search.assert_called_with('+type:century +id:*', start=90, rows=10, df='default_search')
        self.check_standard_header(actual)
        self.assertEqual(409, actual.code)
        self.assertEqual(simple_handler._TOO_LARGE_PAGE, actual.reason)

    @testing.gen_test
    def test_get_integration_4(self):
        "ensure the X-Cantus-Fields request header works"
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '3', 'name': 'three', 'type': 'century'})
        expected = {'1': {'id': '1', 'type': 'century'},
                    '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'},
                    'resources': {'1': {'self': 'https://cantus.org/centuries/1/'},
                                  '2': {'self': 'https://cantus.org/centuries/2/'},
                                  '3': {'self': 'https://cantus.org/centuries/3/'}},
                    'sort_order': ['1', '2', '3'],
        }
        expected_fields = ['id', 'type']
        request_header = 'id, type'

        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              headers={'X-Cantus-Fields': request_header})

        self.solr.search.assert_called_once_with('+type:century +id:*', df='default_search', rows=10)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertCountEqual(expected_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_get_integration_5(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Fields': 'id, type,price'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_FIELDS, actual.reason)

    @testing.gen_test
    def test_get_integration_6(self):
        """
        Returns 404 when the resource ID is not found.
        Regression test for GitHub issue #87.
        """
        resource_id = '34324242343423423423423'
        expected_reason = simple_handler._ID_NOT_FOUND.format('century', resource_id)
        request_url = self.get_url('/centuries/{}/'.format(resource_id))

        actual = yield self.http_client.fetch(request_url,
                                              method='GET',
                                              raise_error=False)

        self.solr.search.assert_called_with('+type:century +id:{}'.format(resource_id), df='default_search')
        self.check_standard_header(actual)
        assert 404 == actual.code
        assert expected_reason == actual.reason

    @testing.gen_test
    def test_terminating_slash(self):
        '''
        Check that the results returned from the root URL are the same when the URL ends with a
        slash and when it doesn't. This test doesn't check whether the results are correct.

        Ultimately this is a test of the __main__ module's URL configuration, but that's okay.
        '''
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})

        slash = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET', raise_error=False)
        noslash = yield self.http_client.fetch(self.get_url('/centuries'), method='GET', raise_error=False)

        self.assertEqual(slash.code, noslash.code)
        self.assertEqual(slash.reason, noslash.reason)
        self.assertEqual(slash.headers, noslash.headers)
        self.assertEqual(slash.body, noslash.body)


class TestOptionsIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.options().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        super(TestOptionsIntegration, self).setUp()
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_options_integration_1a(self):
        "ensure the OPTIONS method works as expected ('browse' URL)"
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-Per-Page',
                            'X-Cantus-Page', 'X-Cantus-Sort', 'X-Cantus-Search-Help']
        actual = yield self.http_client.fetch(self.get_url('/genres/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual('GET, HEAD, OPTIONS, SEARCH', actual.headers['Allow'])
        self.assertEqual('GET, HEAD, OPTIONS, SEARCH', actual.headers['Access-Control-Allow-Methods'])
        self.assertEqual(0, len(actual.body))
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())

    @testing.gen_test
    def test_options_integration_2a(self):
        "OPTIONS request for non-existent resource gives 404"
        actual = yield self.http_client.fetch(self.get_url('/genres/nogenre/'),
                                              method='OPTIONS',
                                              raise_error=False)
        self.check_standard_header(actual)
        self.assertEqual(404, actual.code)
        self.solr.search.assert_called_with('+type:genre +id:nogenre', df='default_search')

    @testing.gen_test
    def test_options_integration_2b(self):
        "OPTIONS request for existing resource returns properly ('view' URL)"
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields']
        self.solr.search_se.add('162', {'id': '162'})
        actual = yield self.http_client.fetch(self.get_url('/genres/162/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual('GET, HEAD, OPTIONS', actual.headers['Allow'])
        self.assertEqual('GET, HEAD, OPTIONS', actual.headers['Access-Control-Allow-Methods'])
        self.assertEqual(0, len(actual.body))
        self.solr.search.assert_called_with('+type:genre +id:162', df='default_search')
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())


class TestHeadIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.head().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestHeadIntegration, self).setUp()
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_head_integration_1a(self):
        "test_get_integration_1() but with the HEAD method"
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '3', 'name': 'three', 'type': 'century'})

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='HEAD')

        self.solr.search.assert_called_once_with('+type:century +id:*', df='default_search', rows=10)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertEqual(0, len(actual.body))


class TestVerifyRequestHeaders(shared.TestHandler):
    '''
    Unit tests for SimpleHandler.verify_request_headers().

    Note that I could have combined these things into fewer tests, but I'm trying a new strategy
    to minimize the things tested per test, rather than trying to minimize the number of tests.
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestVerifyRequestHeaders, self).setUp()
        self.request = httpclient.HTTPRequest(url='/zool/', method='GET')
        self.request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), self.request, type_name='century')

    def setup_with_complex(self):
        "replace self.handler with a ComplexHandler instance"
        self.handler = ComplexHandler(self.get_app(), self.request, type_name='chant')

    def test_vrh_template(self, **kwargs):
        '''
        PLEASE READ THIS WHOLE DOCSTRING BEFORE YOU MODIFY ONE OF THESE TESTS.

        This is a template test. Without kwargs, it runs verify_request_headers() with "default"
        settings, as far as that's posssible. Here are the default values for the kwargs:

        - is_browse_request = True
        - include_resources = True
            - exp_include_resources = True
        - fields = None
            - exp_fields = ['id', 'type', 'name', 'description']
                - NOTE: exp_fields is compared against self.required_fields
        - per_page = None
            - exp_per_page = None
        - page = None
            - exp_page = None
        - sort = None
            - exp_sort = None

        **However** if is_browse_request is set to False in the kwargs, "canary" values are used for
        the following header variables, which should be ignored by verify_request_headers():

        - per_page = 'garbage'
            - exp_per_page = 'garbage'
        - page = 'test'
            - exp_page = 'test'
        - sort = 'data'
            - exp_sort = 'data'

        ------------------------

        The following kwargs also exist:

        :kwarg bool mock_send_error: Whether to install a dummy mock onto send_error(). Default is
            True. If you send a Mock object, it will be attached appropriately, so you can run
            assertions on it once this test method returns.
        :kwarg int send_error_count: The number of calls to SimpleHandler.send_error(). Default is
            no calls. This is checked if :meth:`send_error` is a :class:`Mock` object, regardless of
            the setting of "mock_send_error," so that it works even if you mock that method yourself.
            NOTE that if "expected" is False, this default changes to 1.
        :kwarg bool expected: The expected return value of the method. Default is True. NOTE that
            if "expected" is False, checks related to the header fields are skipped, and you should
            check :meth:`send_error` and adjust "send_error_count" as required.
        '''

        def set_default(key, val):
            "Check in kwargs if 'key' is defined; if not, set it to 'val'."
            if key not in kwargs:
                kwargs[key] = val

        # set default kwargs
        set_default('mock_send_error', True)
        set_default('is_browse_request', True)
        set_default('expected', True)
        set_default('include_resources', True)
        set_default('exp_include_resources', True)
        set_default('fields', None)
        set_default('exp_fields', ['id', 'type', 'name', 'description'])
        if kwargs['is_browse_request']:
            set_default('per_page', None)
            set_default('exp_per_page', 10)
            set_default('page', None)
            set_default('exp_page', 1)
            set_default('sort', None)
            set_default('exp_sort', None)
        else:
            set_default('per_page', 'garbage')
            set_default('exp_per_page', 'garbage')
            set_default('page', 'test')
            set_default('exp_page', 'test')
            set_default('sort', 'data')
            set_default('exp_sort', 'data')
        if kwargs['expected'] is False:
            set_default('send_error_count', 1)
        else:
            set_default('send_error_count', 0)

        if kwargs['mock_send_error'] is True:
            mock_send_error = mock.Mock()
            self.handler.send_error = mock_send_error
        elif kwargs['mock_send_error']:
            self.handler.send_error = kwargs['mock_send_error']
        self.handler.hparams['fields'] = kwargs['fields']
        self.handler.hparams['per_page'] = kwargs['per_page']
        self.handler.hparams['page'] = kwargs['page']
        self.handler.hparams['sort'] = kwargs['sort']
        self.handler.hparams['include_resources'] = kwargs['include_resources']

        actual = self.handler.verify_request_headers(kwargs['is_browse_request'])

        self.assertEqual(kwargs['expected'], actual)
        if kwargs['expected'] is True:
            self.assertEqual(kwargs['exp_fields'], self.handler.returned_fields)
            self.assertEqual(kwargs['exp_per_page'], self.handler.hparams['per_page'])
            self.assertEqual(kwargs['exp_page'], self.handler.hparams['page'])
            self.assertEqual(kwargs['exp_sort'], self.handler.hparams['sort'])
            self.assertEqual(kwargs['exp_include_resources'], self.handler.hparams['include_resources'])
        if isinstance(self.handler.send_error, mock.Mock):
            self.assertEqual(kwargs['send_error_count'], self.handler.send_error.call_count)


    def test_not_browse_request_1(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['fields'] is None (its default)
        - self.hparams['include_resources'] is True (its default)
        - other fields have invalid canary values

        Postconditions:
        - they're both still the same
        - all the other fields still have canary values
        - method returns True
        '''
        self.test_vrh_template(is_browse_request=False)

    @mock.patch('abbot.util.parse_fields_header')
    def test_not_browse_request_2(self, mock_pfh):
        '''
        Preconditions:
        - self.hparams['fields'] is some value
        - parse_fields_header mock returns fine

        Postconditions:
        - they're both still None
        - all the other fields still have canary values
        - method returns True
        '''
        fields = 'something'
        parse_fields_header_return = 'whatever'
        mock_pfh.return_value = parse_fields_header_return

        self.test_vrh_template(is_browse_request=False,
                               fields=fields,
                               exp_fields=parse_fields_header_return)

        mock_pfh.assert_called_once_with('something', ['id', 'type', 'name', 'description'])

    @mock.patch('abbot.util.parse_fields_header')
    def test_not_browse_request_3(self, mock_pfh):
        '''
        Preconditions:
        - self.hparams['fields'] is some value
        - parse_fields_header mock raises ValueError

        Postconditions:
        - send_error() is called
        - method returns False
        '''
        fields = 'something'
        mock_pfh.side_effect = ValueError
        mock_send_error = mock.Mock()

        self.test_vrh_template(is_browse_request=False,
                               fields=fields,
                               expected=False,
                               mock_send_error=mock_send_error)

        mock_pfh.assert_called_once_with('something', ['id', 'type', 'name', 'description'])
        mock_send_error.assert_called_with(400, reason=simple_handler._INVALID_FIELDS)

    def test_not_browse_request_4(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['include_resources'] is '  faLSe  '
        - other fields have invalid canary values

        Postconditions:
        - self.hparams['include_resources'] becomes False
        - method returns True
        '''
        self.test_vrh_template(is_browse_request=False,
                               include_resources='  faLSe  ',
                               exp_include_resources=False)

    def test_not_browse_request_5(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['include_resources'] is '  TRue  '
        - other fields have invalid canary values

        Postconditions:
        - self.hparams['include_resources'] becomes True
        - method returns True
        '''
        self.test_vrh_template(is_browse_request=False,
                               include_resources='  TRue  ',
                               exp_include_resources=True)

    def test_not_browse_request_6(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['include_resources'] is 'wristwatch'
        - other fields have invalid canary values

        Postconditions:
        - method returns False
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(is_browse_request=False,
                               include_resources='wristwatch',
                               expected=False,
                               mock_send_error=mock_send_error)
        mock_send_error.assert_called_with(400, reason=simple_handler._BAD_INCLUDE_RESOURCES)

    def test_browse_request_1(self):
        '''
        Preconditions:
        - per_page is an int (as a string when inputted) in the valid range

        Postconditions:
        - per_page becomes an actual int
        '''
        self.test_vrh_template(per_page='14', exp_per_page=14)

    def test_browse_request_2(self):
        '''
        Preconditions:
        - per_page isn't an int

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, per_page='five')
        mock_send_error.assert_called_with(400, reason=simple_handler._INVALID_PER_PAGE)

    def test_browse_request_3(self):
        '''
        Preconditions:
        - per_page is an int, but less than zero

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, per_page='-3')
        mock_send_error.assert_called_with(400, reason=simple_handler._TOO_SMALL_PER_PAGE)

    def test_browse_request_4(self):
        '''
        Preconditions:
        - per_page is an int, but greater than _MAX_PER_PAGE

        Postconditions:
        - send_error() called *with 507*
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, per_page='40000000')
        mock_send_error.assert_called_with(507,
                                           reason=simple_handler._TOO_BIG_PER_PAGE,
                                           per_page=SimpleHandler._MAX_PER_PAGE)

    def test_browse_request_5(self):
        '''
        Preconditions:
        - per_page is 0

        Postconditions:
        - per_page becomes _MAX_PER_PAGE
        '''
        self.test_vrh_template(per_page='0', exp_per_page=SimpleHandler._MAX_PER_PAGE)

    def test_browse_request_6(self):
        '''
        Preconditions:
        - page is not an int

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, page='two')
        mock_send_error.assert_called_with(400, reason=simple_handler._INVALID_PAGE)

    def test_browse_request_7(self):
        '''
        Preconditions:
        - page is an int (as a string when inputted) greater than 1

        Postconditions:
        - it is returned fine
        '''
        self.test_vrh_template(page='2', exp_page=2)

    def test_browse_request_8(self):
        '''
        Preconditions:
        - page is an int, but 1

        Postconditions:
        - it is returned fine
        '''
        self.test_vrh_template(page='1', exp_page=1)

    def test_browse_request_9(self):
        '''
        Preconditions:
        - page is an int, less than 1

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, page='0')
        mock_send_error.assert_called_with(400, reason=simple_handler._TOO_SMALL_PAGE)

    def test_browse_request_10(self):
        '''
        Preconditions:
        - sort is valid

        Postconditions:
        - returns fine
        '''
        self.test_vrh_template(sort='name,asc', exp_sort='name asc')

    def test_browse_request_11(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises ValueError with _MISSING_DIRECTION_SPEC

        Postconditions:
        - send_error() called with _MISSING_DIRECTION_SPEC
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='name')
        mock_send_error.assert_called_with(400, reason=simple_handler._MISSING_DIRECTION_SPEC)

    def test_browse_request_12(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises ValueError because of an invalid character

        Postconditions:
        - send_error() called with _DISALLOWED_CHARACTER_IN_SORT
        '''
        mock_send_error = mock.Mock()
        exp_reason = simple_handler._DISALLOWED_CHARACTER_IN_SORT
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='n!me,asc')
        mock_send_error.assert_called_with(400, reason=exp_reason)

    def test_browse_request_13(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises KeyError

        Postconditions:
        - send_error() called with _UNKNOWN_FIELD
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='nime,asc')
        mock_send_error.assert_called_with(400, reason=simple_handler._UNKNOWN_FIELD)

    def test_browse_request_14(self):
        '''
        Preconditions:
        - per_page is '-4'
        - page is 'yes'
        - it's a ComplexHandler

        Postconditions:
        - send_error() called with _TOO_SMALL_PER_PAGE; _INVALID_PAGE
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, use_complex_handler=True,
                               per_page='-4', page='yes')
        mock_send_error.assert_called_with(400,
                                           reason=simple_handler._MANY_BAD_HEADERS,
                                           body=[simple_handler._TOO_SMALL_PER_PAGE,
                                                 simple_handler._INVALID_PAGE])


class TestMakeResponseHeaders(shared.TestHandler):
    '''
    Unit tests for SimpleHandler.make_response_headers().

    Note that I could have combined these things into fewer tests, but I'm trying a new strategy
    to minimize the things tested per test, rather than trying to minimize the number of tests.

    Like the tests for :meth:`verify_request_headers`, these tests use a template. Here, I've only
    made additional test methods for the non-default conditions
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestMakeResponseHeaders, self).setUp()
        self.request = httpclient.HTTPRequest(url='/zool/', method='GET')
        self.request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), self.request, type_name='century')

    def test_mrh_template(self, **kwargs):
        '''
        This is a test template for make_response_headers(). By default, the template makes several
        assertions by itself, which are described below.

        You can change a default precondition or the by using the kwargs listed here:
        is_browse_request, num_records, field_counts, include_resources, no_xref, total_results,
        per_page, page, sort.

        You can change the expected hader value by using the kwargs listed here:
        h_fields, h_extra_fields, h_include_resources, h_no_xref, h_total_results, h_per_page,
        h_page, h_sort.

        NOTE that if you set one of the expected header values to ``None``, it is turned into an
        assertion that :meth:`add_header` was not called with that header.

        --------

        These are the "default" pre- and post-conditions.

        Preconditions:
        - is_browse_request is False
        - num_records is 0
        - self.field_counts is {}
        - self.hparams['include_resources'] is True
        - self.hparams['no_xref'] is False

        Postconditions:
        - X-Cantus-Fields isn't called
        - X-Cantus-Extra-Fields isn't called called
        - X-Cantus-Include_Resources called with 'true'
        - X-Cantus-No-Xref isn't called

        --------

        If the "is_browse_request" kwarg is True (not the default), these conditions also apply.

        Additional Preconditions if "is_browse_request" is True:
        - self.total_results is 400
        - self.handler.hparams['per_page'] is None
        - self.hparams['page'] is None
        - self.hparams['sort'] is None

        Additional Postconditions if "is_browse_request" is True:
        - X-Cantus-Total-Results called with 400
        - X-Cantus-Per-Page called with 10
        - X-Cantus-Page called with 1
        - X-Cantus-Sort isn't called
        '''

        def set_default(key, val):
            "Check in kwargs if 'key' is defined; if not, set it to 'val'."
            if key not in kwargs:
                kwargs[key] = val

        # set default values for the kwargs
        set_default('is_browse_request', False)
        set_default('num_records', 0)
        set_default('field_counts', {})
        set_default('include_resources', True)
        set_default('no_xref', False)
        set_default('h_fields', None)
        set_default('h_extra_fields', None)
        set_default('h_include_resources', 'true')
        set_default('h_no_xref', None)
        if kwargs['is_browse_request']:
            set_default('total_results', 400)
            set_default('per_page', None)
            set_default('page', None)
            set_default('sort', None)
            set_default('h_total_results', 400)
            set_default('h_per_page', 10)
            set_default('h_page', 1)
            set_default('h_sort', None)

        # prepare the pre-conditions
        self.handler.field_counts = kwargs['field_counts']
        self.handler.hparams['include_resources'] = kwargs['include_resources']
        self.handler.hparams['no_xref'] = kwargs['no_xref']
        if kwargs['is_browse_request']:
            self.handler.total_results = kwargs['total_results']
            self.handler.hparams['per_page'] = kwargs['per_page']
            self.handler.hparams['page'] = kwargs['page']
            self.handler.hparams['sort'] = kwargs['sort']

        # run the test
        mock_add_header = mock.Mock()
        self.handler.add_header = mock_add_header
        self.handler.make_response_headers(kwargs['is_browse_request'], kwargs['num_records'])

        # check the headers (that are always present)
        header_correspondences = {'h_fields': 'X-Cantus-Fields',
                                  'h_extra_fields': 'X-Cantus-Extra-Fields',
                                  'h_include_resources': 'X-Cantus-Include-Resources',
                                  'h_no_xref': 'X-Cantus-No-Xref'}
        for key, header in header_correspondences.items():
            if kwargs[key] is None:
                assert mock.call(header, mock.ANY) not in mock_add_header.call_args_list
            elif 'h_fields' == key or 'h_extra_fields' == key:
                # we accept any order for these header values, so it's a little complicated to test
                mock_add_header.assert_any_call(header, mock.ANY)
                for each_call in mock_add_header.call_args_list:
                    if header == each_call[0][0]:
                        self.assertCountEqual(kwargs[key].split(','), each_call[0][1].split(','))
                        break
            else:
                mock_add_header.assert_any_call(header, kwargs[key])

        # check the headers (only if is_browse_request)
        if not kwargs['is_browse_request']:
            return
        header_correspondences = {'h_total_results': 'X-Cantus-Total-Results',
                                  'h_per_page': 'X-Cantus-Per-Page',
                                  'h_page': 'X-Cantus-Page',
                                  'h_sort': 'X-Cantus-Sort'}
        for key, header in header_correspondences.items():
            if kwargs[key] is None:
                assert mock.call(header, mock.ANY) not in mock_add_header.call_args_list
            else:
                mock_add_header.assert_any_call(header, kwargs[key])

    def test_basic_browse_request(self):
        '''
        Calls test_mrh_template() with "is_browse_request" set to True.
        '''
        self.test_mrh_template(is_browse_request=True)

    def test_fields_1(self):
        '''
        Preconditions:
        - num_records is 5
        - self.field_counts has these counts
            - 'name': 5
            - 'id': 5
            - 'feast_code': 3
            - 'type': 3

        Postconditions:
        - X-Cantus-Fields called with something like 'id,name,type'
        - X-Cantus-Extra-Fields called with 'feast_code'
        '''
        self.test_mrh_template(num_records=5,
                               field_counts={'name': 5, 'id': 5, 'feast_code': 3, 'type': 3},
                               h_fields='id,name',
                               h_extra_fields='feast_code,type')

    def test_fields_2(self):
        '''
        Preconditions:
        - num_records is 5
        - self.field_counts has these counts
            - 'name': 5
            - 'id': 5
            - 'feast_code': 5
            - 'type': 5

        Postconditions:
        - X-Cantus-Fields called with something like 'id,name,source,type'
        '''
        self.test_mrh_template(num_records=5,
                               field_counts={'name': 5, 'id': 5, 'feast_code': 5, 'type': 5},
                               h_fields='id,name,type,feast_code')

    def test_resources(self):
        '''
        Preconditions:
        - self.hparams['include_resources'] is False

        Postconditions:
        - self.add_header('X-Cantus-Include-Resources', 'false')
        '''
        self.test_mrh_template(include_resources=False,
                               h_include_resources='false')

    def test_xref_1(self):
        '''
        Preconditions:
        - self.hparams['no_xref'] is True

        Postconditions:
        - X-Cantus-No-Xref with 'true'
        '''
        self.test_mrh_template(no_xref=True, h_no_xref='true')

    def test_total_results(self):
        '''
        Preconditions:
        - is_browse_request is True
        - self.total_results is 50

        Postconditions:
        - X-Cantus-Total-Results with 50
        '''
        self.test_mrh_template(is_browse_request=True, total_results=50, h_total_results=50)

    def test_per_page(self):
        '''
        Preconditions:
        - is_browse_request is True
        - self.handler.hparams['per_page'] is 14

        Postconditions:
        - X-Cantus-Per-Page with 14
        '''
        self.test_mrh_template(is_browse_request=True, per_page=14, h_per_page=14)

    def test_page(self):
        '''
        Preconditions:
        - is_browse_request is True
        - self.hparams['page'] is 8

        Postconditions:
        - X-Cantus-Page with 8
        '''
        self.test_mrh_template(is_browse_request=True, page=8, h_page=8)

    @mock.patch('abbot.util.postpare_formatted_sort')
    def test_sort(self, mock_pfs):
        '''
        Preconditions:
        - is_browse_request is True
        - self.hparams['sort'] is 'testing sort'

        Postconditions:
        - postpare_formatted_sort() called with 'testing sort' (mock returns 'sorted')
        - X-Cantus-Sort with 'sorted'
        '''
        mock_pfs.return_value = 'sorted'
        self.test_mrh_template(is_browse_request=True, sort='testing sort', h_sort='sorted')
        mock_pfs.assert_called_once_with('testing sort')


class TestSearchUnit(shared.TestHandler):
    '''
    Tests for SimpleHandler.search_handler() and search().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSearchUnit, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')
        self.handler.hparams['search_query'] = 'some query'

    @mock.patch('abbot.util.run_subqueries')
    @mock.patch('abbot.simple_handler.SimpleHandler.get_handler')
    @testing.gen_test
    def test_search_handler_1(self, mock_get_handler, mock_rs):
        '''
        Ensure the kwargs are passed along properly.
        '''
        expected = ('five', 5)
        mock_get_handler.return_value = shared.make_future(expected)
        self.handler.hparams['search_query'] = 'feast:celery genre:tasty'
        mock_rs.return_value = shared.make_future([('feast', 'celery'), 'AND', ('genre', 'tasty')])
        expected_final_query = 'feast:celery  AND genre:tasty '  # what's sent on to get_handler()

        actual = yield self.handler.search_handler()

        assert expected == actual
        mock_get_handler.assert_called_once_with(query=expected_final_query)

    @mock.patch('abbot.util.run_subqueries')
    @mock.patch('abbot.simple_handler.SimpleHandler.get_handler')
    @mock.patch('abbot.simple_handler.SimpleHandler.send_error')
    @testing.gen_test
    def test_search_handler_2(self, mock_senderr, mock_get_handler, mock_rs):
        '''
        Ensure a 404 error when a subquery has no results.

        This is a regression test for GitHub issue #55.
        '''
        mock_rs.side_effect = util.InvalidQueryError

        actual = yield self.handler.search_handler()

        mock_senderr.assert_called_once_with(404, reason=simple_handler._NO_SEARCH_RESULTS)
        assert 0 == mock_get_handler.call_count
        assert actual is None

    @mock.patch('abbot.simple_handler.SimpleHandler.get_handler')
    @mock.patch('abbot.simple_handler.SimpleHandler.send_error')
    @testing.gen_test
    def test_search_handler_3(self, mock_senderr, mock_get_handler):
        '''
        Ensure a 400 error when given an invalid query string.

        This is a regression test for GitHub issue #74.
        '''
        query = 'feast: genre:Absalon'
        self.handler.hparams['search_query'] = query

        actual = yield self.handler.search_handler()

        assert actual is None
        assert 0 == mock_get_handler.call_count
        mock_senderr.assert_called_with(400, reason=simple_handler._INVALID_SEARCH_QUERY)

    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_1(self, mock_search_handler):
        '''
        self.hparam['search_query'] is None: return None, don't call search_handler()
        '''
        self.handler.hparams['search_query'] = None
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        self.assertEqual(0, mock_search_handler.call_count)

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_2(self, mock_search_handler, mock_vrh):
        '''
        verify_request_headers() returns False: return None, don't call search_handler()
        '''
        mock_vrh.return_value = False
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        self.assertEqual(0, mock_search_handler.call_count)

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_3(self, mock_search_handler, mock_vrh):
        '''
        search_handler() raises SolrError; return None, call send_error()
        '''
        mock_vrh.return_value = True
        mock_search_handler.side_effect = pysolrtornado.SolrError
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        mock_search_handler.assert_called_once_with()

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_4(self, mock_search_handler, mock_vrh):
        '''
        search_handler() returns None; return None
        '''
        mock_vrh.return_value = True
        mock_search_handler.return_value = shared.make_future((None, 0))
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        mock_search_handler.assert_called_once_with()

    @mock.patch('abbot.simple_handler.SimpleHandler.make_response_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.write')
    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_5(self, mock_search_handler, mock_vrh, mock_write, mock_mrh):
        '''
        search_handler() returns 3 things, "include_resources" is False, is a HEAD request;
        don't call write(), call make_response_headers() with proper arguments
        '''
        self.handler.hparams['include_resources'] = False
        self.handler.head_request = True
        mock_vrh.return_value = True
        mock_search_handler.return_value = shared.make_future(([1, 2, 3], 42))
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        mock_search_handler.assert_called_once_with()
        self.assertEqual(0, mock_write.call_count)
        mock_mrh.assert_called_once_with(True, 42)

    @mock.patch('abbot.simple_handler.SimpleHandler.make_response_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.write')
    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_6(self, mock_search_handler, mock_vrh, mock_write, mock_mrh):
        '''
        search_handler() returns 3 things, "include_resources" is True, is not a HEAD request;
        call write(), call make_response_headers() with proper arguments
        '''
        self.handler.hparams['include_resources'] = True
        self.handler.head_request = False
        mock_vrh.return_value = True
        mock_search_handler.return_value = shared.make_future(([1, 2, 3, 'resources'], 42))
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        mock_search_handler.assert_called_once_with()
        mock_write.assert_called_once_with([1, 2, 3, 'resources'])
        mock_mrh.assert_called_once_with(True, 42)


class TestSendError(shared.TestHandler):
    '''
    Tests for SimpleHandler.send_error().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSendError, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbot.simple_handler.SimpleHandler.clear')
    @mock.patch('abbot.simple_handler.SimpleHandler.add_header')
    @mock.patch('abbot.simple_handler.SimpleHandler.set_status')
    @mock.patch('abbot.simple_handler.SimpleHandler.write')
    def test_send_error_1(self, mock_write, mock_set_status, mock_add_header, mock_clear):
        '''
        per_page, reason, and response kwargs are all provided.

        Ensure:
        - clear() is called
        - add_header() called with appropriate args
        - set_status() called with appropriate args
        - write() called with appropriate args
        '''
        code = 418
        reason = 'This is a test.'
        per_page = 42
        response = 'Please avoid panicking about this test error.'

        self.handler.send_error(code, reason=reason, per_page=per_page, response=response)

        mock_clear.assert_called_once_with()
        mock_add_header.assert_called_once_with('X-Cantus-Per-Page', per_page)
        mock_set_status.assert_called_once_with(code, reason)
        mock_write.assert_called_once_with(response)

    @mock.patch('abbot.simple_handler.SimpleHandler.clear')
    @mock.patch('abbot.simple_handler.SimpleHandler.add_header')
    @mock.patch('abbot.simple_handler.SimpleHandler.set_status')
    @mock.patch('abbot.simple_handler.SimpleHandler.write')
    def test_send_error_2(self, mock_write, mock_set_status, mock_add_header, mock_clear):
        '''
        per_page, reason, and response kwargs are all omitted.

        Ensure:
        - clear() is called
        - add_header() not called
        - set_status() called with appropriate args            code)
        - write() called with appropriate args                 'code: (no reason given)')
        '''
        code = 418

        self.handler.send_error(code)

        mock_clear.assert_called_once_with()
        self.assertEqual(0, mock_add_header.call_count)
        mock_set_status.assert_called_once_with(code)
        mock_write.assert_called_once_with('{}: (no reason given)'.format(code))
