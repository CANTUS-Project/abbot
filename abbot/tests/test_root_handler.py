#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_root_handler.py
# Purpose:                Tests for the Abbot server's RootHandler.
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
Tests for the Abbot server's RootHandler.
'''

# pylint: disable=protected-access
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

from unittest import mock
from tornado import escape, httpclient, options, testing
from abbot import handlers
import shared


class TestRootHandler(shared.TestHandler):
    '''
    Tests for the RootHandler.
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestRootHandler, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.RootHandler(self.get_app(), request)

    def test_root_1(self):
        "basic test"
        server_name = options.options.server_name
        all_plural_resources = [
            'centuries',
            'chants',
            'feasts',
            'genres',
            'indexers',
            'notations',
            'offices',
            'portfolia',
            'provenances',
            'sigla',
            'segments',
            'sources',
            'source_statii'
            ]
        expected = {'browse': {}, 'view': {}}
        for term in all_plural_resources:
            expected['view'][term] = '{}{}/id?/'.format(server_name, term)
            expected['browse'][term] = '{}{}/'.format(server_name, term)
        expected['view']['source_statii'] = '{}statii/id?/'.format(server_name)
        expected['browse']['source_statii'] = '{}statii/'.format(server_name)
        expected['browse']['all'] = '{}browse/'.format(server_name)
        expected = {'resources': expected}

        actual = self.handler.prepare_get()

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_root_2(self):
        "integration test for test_root_1()"
        server_name = options.options.server_name
        all_plural_resources = [
            'centuries',
            'chants',
            'feasts',
            'genres',
            'indexers',
            'notations',
            'offices',
            'portfolia',
            'provenances',
            'sigla',
            'segments',
            'sources',
            'source_statii'
            ]
        expected = {'browse': {}, 'view': {}}
        for term in all_plural_resources:
            expected['view'][term] = '{}{}/id?/'.format(server_name, term)
            expected['browse'][term] = '{}{}/'.format(server_name, term)
        expected['view']['source_statii'] = '{}statii/id?/'.format(server_name)
        expected['browse']['source_statii'] = '{}statii/'.format(server_name)
        expected['browse']['all'] = '{}browse/'.format(server_name)
        expected = {'resources': expected}

        actual = yield self.http_client.fetch(self.get_url('/'), method='GET')

        self.assertEqual(expected, escape.json_decode(actual.body))
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'].lower())

    @testing.gen_test
    def test_options_integration_1(self):
        "ensure the OPTIONS method works as expected"
        actual = yield self.http_client.fetch(self.get_url('/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual(handlers.RootHandler._ALLOWED_METHODS, actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))

    @testing.gen_test
    def test_terminating_slash(self):
        '''
        Check that the results returned from the root URL are the same when the URL ends with a
        slash and when it doesn't. This test doesn't check whether the results are correct.
        '''
        slash = yield self.http_client.fetch(self.get_url('/'), method='GET', raise_error=False)
        noslash = yield self.http_client.fetch(self.get_url(''), method='GET', raise_error=False)
        self.assertEqual(slash.code, noslash.code)
        self.assertEqual(slash.reason, noslash.reason)
        self.assertEqual(slash.headers, noslash.headers)
        self.assertEqual(slash.body, noslash.body)
        self.check_standard_header(slash)
        self.check_standard_header(noslash)


class TestCanonicalHandler(shared.TestHandler):
    '''
    Tests for the CanonicalHandler.
    '''

    @testing.gen_test
    def test_get_1(self):
        '''
        Ensure the redirect works properly with a GET request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher'), method='GET',
                                              follow_redirects=False, raise_error=False)
        self.assertEqual(301, actual.code)
        self.assertEqual('/christopher/', actual.headers['Location'])
        self.check_standard_header(actual)

    @testing.gen_test
    def test_get_2(self):
        '''
        Ensure a 400 when the URL has a query string that's not /-terminated.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher?zed'), method='GET',
                                              follow_redirects=False, raise_error=False)
        self.assertEqual(400, actual.code)
        self.check_standard_header(actual)

    @testing.gen_test
    def test_get_3(self):
        '''
        Ensure a 400 when the URL has a query string that's /-terminated.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher?zed/'), method='GET',
                                              follow_redirects=False, raise_error=False)
        self.assertEqual(400, actual.code)
        self.check_standard_header(actual)

    @testing.gen_test
    def test_get_4(self):
        '''
        Ensure a 404 with a GET request with a query string that ends with / and the URL already
        ends with /.

        One might expect a 400 response here because of the ? in the URL, but it doesn't really
        matter. The point of this test is to guarantee that a request like this fails cleanly.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher/?zed/'), method='GET',
                                              follow_redirects=False, raise_error=False)
        self.assertEqual(404, actual.code)
        self.check_standard_header(actual)

    @testing.gen_test
    def test_head(self):
        '''
        Ensure the redirect works properly with a HEAD request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher'), method='HEAD',
                                              follow_redirects=False, raise_error=False)
        self.assertEqual(301, actual.code)
        self.assertEqual('/christopher/', actual.headers['Location'])
        self.check_standard_header(actual)

    @testing.gen_test
    def test_options(self):
        '''
        Ensure the redirect works properly with a OPTIONS request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher'), method='OPTIONS',
                                              follow_redirects=False, raise_error=False)
        self.assertEqual(301, actual.code)
        self.assertEqual('/christopher/', actual.headers['Location'])
        self.check_standard_header(actual)

    @testing.gen_test
    def test_search(self):
        '''
        Ensure the redirect works properly with a SEARCH request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher'), method='SEARCH',
                                              follow_redirects=False, raise_error=False,
                                              allow_nonstandard_methods=True)
        self.assertEqual(301, actual.code)
        self.assertEqual('/christopher/', actual.headers['Location'])
        self.check_standard_header(actual)


class TestEverythingElseHandler(shared.TestHandler):
    '''
    Tests for the EverythingElseHandler, for requests that don't match another handler.
    '''

    @testing.gen_test
    def test_get(self):
        '''
        Ensure the 404 works properly with a GET request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher/'), method='GET',
                                              follow_redirects=False, raise_error=False)
        assert 404 == actual.code
        assert b'404: Not Found' == actual.body
        self.check_standard_header(actual)

    @testing.gen_test
    def test_head(self):
        '''
        Ensure the 404 works properly with a HEAD request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher/'), method='HEAD',
                                              follow_redirects=False, raise_error=False)
        assert 404 == actual.code
        self.check_standard_header(actual)

    @testing.gen_test
    def test_options(self):
        '''
        Ensure the 404 works properly with a OPTIONS request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher/'), method='OPTIONS',
                                              follow_redirects=False, raise_error=False)
        assert 404 == actual.code
        assert b'404: Not Found' == actual.body
        self.check_standard_header(actual)

    @testing.gen_test
    def test_search(self):
        '''
        Ensure the 404 works properly with a SEARCH request.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher/'), method='SEARCH',
                                              follow_redirects=False, raise_error=False,
                                              allow_nonstandard_methods=True)
        assert 404 == actual.code
        assert b'404: Not Found' == actual.body
        self.check_standard_header(actual)

    @testing.gen_test
    def test_put(self):
        '''
        PUT requests aren't allowed at the root URL; expect a 405.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher/'), method='PUT',
                                              follow_redirects=False, raise_error=False,
                                              allow_nonstandard_methods=True)
        assert 405 == actual.code
        self.check_standard_header(actual)

    @testing.gen_test
    def test_post(self):
        '''
        POST requests aren't allowed at the root URL; expect a 405.
        '''
        actual = yield self.http_client.fetch(self.get_url('/christopher/'), method='POST',
                                              follow_redirects=False, raise_error=False,
                                              allow_nonstandard_methods=True)
        assert 405 == actual.code
        self.check_standard_header(actual)
