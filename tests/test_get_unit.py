#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_get_unit.py
# Purpose:                Unit tests for GET requests in SimpleHandler and ComplexHandler.
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
Unit tests for GET requests in SimpleHandler and ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock
import pysolrtornado
from tornado import httpclient, testing

from abbot import simple_handler
from abbot.simple_handler import SimpleHandler
import shared


class TestBasicGetSimple(shared.TestHandler):
    '''
    Unit tests for the SimpleHandler.basic_get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestBasicGetSimple, self).setUp()
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


class TestGetSimple(shared.TestHandler):
    '''
    Unit tests for the SimpleHandler.get() and SimpleHandler.get_handler().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestGetSimple, self).setUp()
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
