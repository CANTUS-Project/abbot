#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_head.py
# Purpose:                Tests for HEAD requests in SimpleHandler and ComplexHandler.
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
Tests for HEAD requests in SimpleHandler and ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from tornado import testing

import shared


class TestSimpleIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.head().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSimpleIntegration, self).setUp()
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
