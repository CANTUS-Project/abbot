#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_search_integration.py
# Purpose:                Integration tests for SEARCH requests in SimpleHandler and ComplexHandler.
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
Integration tests for SEARCH requests in SimpleHandler and ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

import test_get_integration


# TODO: these tests *in addition to* the GET ones
# - when there's no query submitted
# - when there's an invalid query submitted
# - when the query returns no results
# - SEARCH query on a "view" URL leads to failure
# - queries that:
#   - are just looked up and work (done in other suite, but I should mention that specifically)
#   - require subqueries
#   - require complicated parsing


class TestSimple(test_get_integration.TestSimple):
    '''
    Runs the GET method's TestSimple suite with the SEARCH HTTP method.
    '''

    def __init__(self, *args, **kwargs):
        super(TestSimple, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    # TODO: add tests for SEARCH-specific functionality


class TestComplex(test_get_integration.TestComplex):
    '''
    Runs the GET method's TestComplex suite with the SEARCH HTTP method.
    '''

    def __init__(self, *args, **kwargs):
        super(TestComplex, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    # TODO: add tests for SEARCH-specific functionality
    # TODO: make sure the tests added in *this module's* Simple tests are also run with Complex


class TestBadRequestHeadersSimple(test_get_integration.TestBadRequestHeadersSimple):
    '''
    Runs the GET method's TestBadRequestHeadersSimple suite with the SEARCH HTTP method.
    '''

    def __init__(self, *args, **kwargs):
        super(TestBadRequestHeadersSimple, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    # TODO: add tests for SEARCH-specific headers


class TestBadRequestHeadersComplex(test_get_integration.TestBadRequestHeadersComplex):
    '''
    Runs the GET method's TestBadRequestHeadersSimple suite with the SEARCH HTTP method.
    '''

    def __init__(self, *args, **kwargs):
        super(TestBadRequestHeadersComplex, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    # TODO: make sure the tests added in *this module's* Simple tests are also run with Complex
