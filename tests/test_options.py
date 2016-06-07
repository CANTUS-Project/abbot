#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_options.py
# Purpose:                Tests for OPTIONS requests in SimpleHandler and ComplexHandler.
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
Tests for OPTIONS requests in SimpleHandler and ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock

import pysolrtornado
from tornado import testing

from abbot import simple_handler
import shared


class TestSimpleIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.options().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        super(TestSimpleIntegration, self).setUp()
        self.solr = self.setUpSolr()
        self.rtype = 'genres'

    @testing.gen_test
    def test_browse_works(self):
        '''
        ensure the OPTIONS method works as expected ('browse' URL)
        '''
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-Per-Page',
                            'X-Cantus-Page', 'X-Cantus-Sort']
        actual = yield self.http_client.fetch(self.get_url('/{}/'.format(self.rtype)), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual('GET, HEAD, OPTIONS, SEARCH', actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())

    @testing.gen_test
    def test_view_works(self):
        '''
        OPTIONS request for existing resource returns properly ('view' URL)
        '''
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields']
        self.solr.search_se.add('162', {'id': '162'})
        actual = yield self.http_client.fetch(self.get_url('/{}/162/'.format(self.rtype)), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual('GET, HEAD, OPTIONS', actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))
        self.solr.search.assert_called_with('+type:{} +id:162'.format(self.rtype[:-1]),
            df='default_search')
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())

    @testing.gen_test
    def test_nonexistent_resource(self):
        '''
        OPTIONS request for non-existent resource gives 404
        '''
        actual = yield self.http_client.fetch(self.get_url('/{}/nogenre/'.format(self.rtype)),
                                              method='OPTIONS',
                                              raise_error=False)
        self.check_standard_header(actual)
        self.assertEqual(404, actual.code)
        self.solr.search.assert_called_with('+type:{} +id:nogenre'.format(self.rtype[:-1]),
            df='default_search')

    @testing.gen_test
    def test_invalid_resource(self):
        '''
        OPTIONS request for an invalid resource ID gives 422
        '''
        actual = yield self.http_client.fetch(self.get_url('/{}/nogenre-/'.format(self.rtype)),
                                              method='OPTIONS',
                                              raise_error=False)
        self.check_standard_header(actual)
        self.assertEqual(422, actual.code)
        self.assertEqual(simple_handler._INVALID_ID, actual.reason)
        assert self.solr.search.call_count == 0

    @mock.patch('abbot.simple_handler.log')
    @testing.gen_test
    def test_solr_unavailable(self, mock_log):
        '''
        OPTIONS request for a valid resource ID when Solr is unavailable gives 502
        '''
        solr_error_message = 'blah blah'
        self.solr.search.side_effect = pysolrtornado.SolrError(solr_error_message)
        actual = yield self.http_client.fetch(self.get_url('/{}/162/'.format(self.rtype)),
                                              method='OPTIONS',
                                              raise_error=False)
        self.check_standard_header(actual)
        self.assertEqual(502, actual.code)
        self.assertEqual(simple_handler._SOLR_502_ERROR, actual.reason)
        assert self.solr.search.call_count == 1
        assert solr_error_message in mock_log.warn.call_args_list[0][0][0]

    @testing.gen_test
    def test_cors_preflight_1(self):
        '''
        With a "browse" URL, simulate a CORS preflight request with no Access-Control-Request-Headers
        request header.
        '''
        origin = self._simple_options.cors_allow_origin
        request_headers = {
            'Origin': origin,
            'Access-Control-Request-Method': 'GET',
        }
        actual = yield self.http_client.fetch(self.get_url('/{}/'.format(self.rtype)),
                                              method='OPTIONS',
                                              headers=request_headers)
        #
        assert actual.headers['Access-Control-Allow-Origin'] == origin
        assert actual.headers['Vary'] == 'Origin'
        assert actual.headers['Access-Control-Max-Age'] == '86400'
        assert actual.headers['Access-Control-Allow-Methods'] == 'GET'
        assert 'Access-Control-Allow-Headers' not in actual.headers

    @testing.gen_test
    def test_cors_preflight_2(self):
        '''
        With a "view" URL, simulate a CORS preflight request with a Access-Control-Request-Headers
        request header.
        '''
        self.solr.search_se.add('233', {'id': '233'})
        origin = self._simple_options.cors_allow_origin
        request_headers = {
            'Origin': origin,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'x-cantus-page,CONTENT-TYPE',
        }
        actual = yield self.http_client.fetch(self.get_url('/{}/233/'.format(self.rtype)),
                                              method='OPTIONS',
                                              headers=request_headers)
        #
        assert actual.headers['Access-Control-Allow-Origin'] == origin
        assert actual.headers['Vary'] == 'Origin'
        assert actual.headers['Access-Control-Max-Age'] == '86400'
        assert actual.headers['Access-Control-Allow-Methods'] == 'GET'
        assert actual.headers['Access-Control-Allow-Headers'] == 'x-cantus-page,CONTENT-TYPE'


class TestComplexIntegration(TestSimpleIntegration):
    '''
    Integration tests for the ComplexHandler.options().

    No tests unique to the ComplexHandler.
    '''

    def setUp(self):
        super(TestComplexIntegration, self).setUp()
        self.rtype = 'chants'
