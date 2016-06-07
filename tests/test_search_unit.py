#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_search_unit.py
# Purpose:                Unit tests for SEARCH requests in SimpleHandler and ComplexHandler.
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
Unit tests for SEARCH requests in SimpleHandler and ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

import pysolrtornado
from tornado import httpclient, testing
from unittest import mock

from abbot import simple_handler
from abbot.simple_handler import SimpleHandler
from abbot import util
import shared


class TestSimple(shared.TestHandler):
    '''
    Tests for SimpleHandler.search_handler() and search().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSimple, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')
        self.handler.hparams['search_query'] = 'some query'

    @mock.patch('abbot.util.parse_query')
    @mock.patch('abbot.util.run_subqueries')
    @mock.patch('abbot.simple_handler.SimpleHandler.get_handler')
    @testing.gen_test
    def test_search_handler_1(self, mock_get_handler, mock_rs, mock_parse):
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
        mock_parse.assert_called_with('type:century AND (feast:celery genre:tasty)')
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
        assert (None, 0) == actual

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

        mock_senderr.assert_called_with(400, reason=simple_handler._INVALID_SEARCH_QUERY)
        assert 0 == mock_get_handler.call_count
        assert (None, 0) == actual

    @mock.patch('abbot.simple_handler.SimpleHandler.get_handler')
    @mock.patch('abbot.simple_handler.SimpleHandler.send_error')
    @testing.gen_test
    def test_search_handler_4(self, mock_senderr, mock_get_handler):
        '''
        Ensure a 400 error when util.assemble_query() raises a ValueError because of an invalid field.
        '''
        query = 'gingerbread:Absalon'
        self.handler.hparams['search_query'] = query

        actual = yield self.handler.search_handler()

        mock_senderr.assert_called_with(400, reason=simple_handler._INVALID_SEARCH_FIELD.format('gingerbread'))
        assert 0 == mock_get_handler.call_count
        assert (None, 0) == actual

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

    @mock.patch('abbot.simple_handler.log')
    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_3(self, mock_search_handler, mock_vrh, mock_log):
        '''
        search_handler() raises SolrError; return None, call send_error()
        '''
        solr_error_message = 'blah blah'
        mock_vrh.return_value = True
        mock_search_handler.side_effect = pysolrtornado.SolrError(solr_error_message)
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        mock_search_handler.assert_called_once_with()
        assert solr_error_message in mock_log.warn.call_args_list[0][0][0]

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
        search_handler() returns 3 things, "include_resources" is False,; call write(); call
        make_response_headers() with proper arguments
        '''
        self.handler.hparams['include_resources'] = False
        mock_vrh.return_value = True
        mock_search_handler.return_value = shared.make_future(([1, 2, 3], 42))
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        mock_search_handler.assert_called_once_with()
        mock_write.assert_called_once_with([1, 2, 3])
        mock_mrh.assert_called_once_with(True, 42)

    @mock.patch('abbot.simple_handler.SimpleHandler.make_response_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.write')
    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    @mock.patch('abbot.simple_handler.SimpleHandler.search_handler')
    @testing.gen_test
    def test_search_6(self, mock_search_handler, mock_vrh, mock_write, mock_mrh):
        '''
        search_handler() returns 3 things, "include_resources" is True; call write(); call
        make_response_headers() with proper arguments
        '''
        self.handler.hparams['include_resources'] = True
        mock_vrh.return_value = True
        mock_search_handler.return_value = shared.make_future(([1, 2, 3, 'resources'], 42))
        actual = yield self.handler.search()
        self.assertIsNone(actual)
        mock_search_handler.assert_called_once_with()
        mock_write.assert_called_once_with([1, 2, 3, 'resources'])
        mock_mrh.assert_called_once_with(True, 42)

    @mock.patch('abbot.simple_handler.SimpleHandler.send_error')
    @testing.gen_test
    def test_search_7(self, mock_senderr):
        '''
        When a "resource_id" is given, this is SEARCH on a "view" URL, so search() should call
        send_error() with a 405 Method Not Allowed.
        '''
        self.handler.search(resource_id='123/')
        mock_senderr.assert_called_with(405, allow=SimpleHandler._ALLOWED_VIEW_METHODS)
