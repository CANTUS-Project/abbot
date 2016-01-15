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

import pysolrtornado
from tornado import testing

from abbot import simple_handler

import test_get_integration


# TODO: a test that requires complicated parsing


class TestSimple(test_get_integration.TestSimple):
    '''
    Runs the GET method's TestSimple suite with the SEARCH HTTP method.

    NOTE that the tests written specifically for this suite only need to check the return value when
         it's different from what you might expect in a GET request. The GET integration tests are
         sufficient for normal stuff.
    '''

    def __init__(self, *args, **kwargs):
        super(TestSimple, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    @testing.gen_test
    def test_boringly_works(self):
        '''
        When the query just works properly.
        '''
        # the Century will be searched both for the subquery and the cross-reference
        self.solr.search_se.add('id:830', {'type': 'century', 'id': '830', 'name': '21st century'})

        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              body=b'{"query":"id:830"}')

        self.solr.search.assert_called_with(' +type:{} id:830 '.format(self._type[0]),
            df='default_search', rows=10)
        self.check_standard_header(actual)

    @testing.gen_test
    def test_invalid_search_string(self):
        '''
        When the search string is invalid, and should be refused by util.parse_query().
        '''
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              body=b'{"query":"type:salad AND"}')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_SEARCH_QUERY, actual.reason)

    @testing.gen_test
    def test_no_results(self):
        '''
        When the search returns no results, give 404.
        '''
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              body=b'{"query":"name:Todd"}')

        self.solr.search.assert_called_with(' +type:{} name:Todd '.format(self._type[0]),
            df='default_search', rows=10)
        self.check_standard_header(actual)
        self.assertEqual(404, actual.code)
        self.assertEqual(simple_handler._NO_SEARCH_RESULTS, actual.reason)

    @testing.gen_test
    def test_search_to_view(self):
        '''
        A SEARCH request to a "view" URL will fail with "405 Method Not Allowed."
        '''
        actual = yield self.http_client.fetch('{}7244/'.format(self._browse_url),
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              body=b'{"query":"name:Todd"}')

        self.check_standard_header(actual)
        assert 405 == actual.code
        assert 'Method Not Allowed' == actual.reason
        assert 'GET, HEAD, OPTIONS' == actual.headers['Allow']  # required in RFC 7231 S. 6.5.5


class TestComplex(test_get_integration.TestComplex):
    '''
    Runs the GET method's TestComplex suite with the SEARCH HTTP method.

    NOTE that the tests written specifically for this suite only need to check the return value when
         it's different from what you might expect in a GET request. The GET integration tests are
         sufficient for checking cross-references and the like.
    '''

    def __init__(self, *args, **kwargs):
        super(TestComplex, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    # tests from TestSimple
    test_boringly_works = TestSimple.test_boringly_works
    test_invalid_search_string = TestSimple.test_invalid_search_string
    test_no_results = TestSimple.test_no_results
    test_search_to_view = TestSimple.test_search_to_view

    @testing.gen_test
    def test_subquery_returns_nothing(self):
        "returns 404 when a subquery yields no results"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              body=b'{"query":"century:21st"}')

        # as submitted by run_subqueries()
        self.solr.search.assert_called_with('type:century AND (21st)', df='default_search')
        self.check_standard_header(actual)
        self.assertEqual(404, actual.code)
        self.assertEqual(simple_handler._NO_SEARCH_RESULTS, actual.reason)

    @testing.gen_test
    def test_subquery_returns_one_thing(self):
        '''
        Works properly with a subquery yielding one result.
        '''
        # the Century will be searched both for the subquery and the cross-reference
        self.solr.search_se.add('21st', {'type': 'century', 'id': '830', 'name': '21st century'})
        self.solr.search_se.add('id:830', {'type': 'century', 'id': '830', 'name': '21st century'})
        self.solr.search_se.add('type:source', {'type': 'source', 'id': '999', 'century_id': '830'})

        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              body=b'{"query":"century:21st"}')

        # as submitted by run_subqueries()
        self.solr.search.assert_any_call('type:century AND (21st)', df='default_search')
        # as submitted by the search itself
        self.solr.search.assert_any_call(' +type:source century_id:830 ', df='default_search', rows=10)
        # as submitted for the cross-reference
        self.solr.search.assert_any_call('+type:century +id:830', df='default_search')
        self.check_standard_header(actual)

    @testing.gen_test
    def test_subquery_returns_three_things(self):
        '''
        Works properly with a subquery yielding three results.
        '''
        # the Century will be searched both for the subquery and the cross-reference
        self.solr.search_se.add('21st', {'type': 'century', 'id': '830', 'name': '21st century'})
        self.solr.search_se.add('21st', {'type': 'century', 'id': '831', 'name': '21-1/3s century'})
        self.solr.search_se.add('21st', {'type': 'century', 'id': '832', 'name': '21-2/3s century'})
        self.solr.search_se.add('id:830', {'type': 'century', 'id': '830', 'name': '21st century'})
        self.solr.search_se.add('type:source', {'type': 'source', 'id': '999', 'century_id': '830'})

        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              body=b'{"query":"century:21st"}')

        # as submitted by run_subqueries()
        self.solr.search.assert_any_call('type:century AND (21st)', df='default_search')
        # as submitted by the search itself
        self.solr.search.assert_any_call(' +type:source (century_id:830^3 OR century_id:831^2 OR century_id:832^1) ',
            df='default_search', rows=10)
        # as submitted for the cross-reference
        self.solr.search.assert_any_call('+type:century +id:830', df='default_search')
        self.check_standard_header(actual)

    @testing.gen_test
    def test_solr_failure_in_subquery(self):
        "returns 502 when Solr fails while running a subquery"
        self.solr.search.side_effect = pysolrtornado.SolrError

        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              body=b'{"query":"century:21st"}')

        # as submitted by run_subqueries()
        self.solr.search.assert_called_with('type:century AND (21st)', df='default_search')
        self.check_standard_header(actual)
        self.assertEqual(502, actual.code)
        self.assertEqual(simple_handler._SOLR_502_ERROR, actual.reason)


class TestBadRequestHeadersSimple(test_get_integration.TestBadRequestHeadersSimple):
    '''
    Runs the GET method's TestBadRequestHeadersSimple suite with the SEARCH HTTP method.
    '''

    def __init__(self, *args, **kwargs):
        super(TestBadRequestHeadersSimple, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    @testing.gen_test
    def test_no_query(self):
        "returns 400 when there is no request body"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False)

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._MISSING_SEARCH_BODY, actual.reason)

    @testing.gen_test
    def test_invalid_query(self):
        "returns 400 when the request body isn't valid JSON"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              body=b'<query>Alldkkllleeejjjasjdfajsdfjasdf</query>')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._MISSING_SEARCH_BODY, actual.reason)


class TestBadRequestHeadersComplex(test_get_integration.TestBadRequestHeadersComplex):
    '''
    Runs the GET method's TestBadRequestHeadersSimple suite with the SEARCH HTTP method.
    '''

    def __init__(self, *args, **kwargs):
        super(TestBadRequestHeadersComplex, self).__init__(*args, **kwargs)
        self._method = 'SEARCH'

    # this runs the SEARCH-specific tests from above, but with a ComplexHandler
    test_no_query = TestBadRequestHeadersSimple.test_no_query
    test_invalid_query = TestBadRequestHeadersSimple.test_invalid_query
