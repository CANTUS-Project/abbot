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
from tornado import escape, testing

from abbot import simple_handler

import test_get_integration


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

        self.solr.search.assert_any_call('type:{}  AND  ( id:830  ) '.format(self._type[0]),
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

        self.solr.search.assert_called_with('type:{}  AND  ( name:Todd  ) '.format(self._type[0]),
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

    @testing.gen_test
    def test_invalid_field(self):
        '''
        A SEARCH request with an invalid field in the query will fail with 400.
        '''
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              body=b'{"query":"gingerbread:Absalon"}')

        self.check_standard_header(actual)
        assert 400 == actual.code
        assert simple_handler._INVALID_SEARCH_FIELD.format('gingerbread') == actual.reason


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
        self.solr.search.assert_any_call('type:source  AND  ( century_id:830  ) ', df='default_search', rows=10)
        # as submitted for the cross-reference
        self.solr.search.assert_any_call('id:830', df='default_search', rows=1)
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
        self.solr.search.assert_any_call('type:source  AND  ( (century_id:830^3 OR century_id:831^2 OR century_id:832^1)  ) ',
            df='default_search', rows=10)
        # as submitted for the cross-reference
        self.solr.search.assert_any_call('id:830', df='default_search', rows=1)
        self.check_standard_header(actual)

    @testing.gen_test
    def test_solr_failure_in_subquery(self):
        "returns 502 when Solr fails while running a subquery"
        self.solr.search.side_effect = pysolrtornado.SolrError('fail!')

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

    @testing.gen_test
    def test_issue_96(self):
        '''
        This is a regression test for GitHub issue #96.

        In this issue, cross-references to Notation resources were found to be incorrect. This test
        is to guarantee proper behaviour for the /browse/ URL.

        NOTE: the important part is the "resources" URL generated for the "notation_style" xref.
        '''
        self.solr.search_se.add('id:3895', {'type': 'notation', 'name': 'German - neumatic', 'id': '3895'})
        self.solr.search_se.add('id:123', {'type': 'source', 'id': '123', 'notation_style_id': '3895'})
        headers = {'X-Cantus-Include-Resources': 'true'}
        exp_ids = ['123']

        actual = yield self.http_client.fetch(self.get_url('/browse/'), method='SEARCH',
            allow_nonstandard_methods=True, body=b'{"query":"+id:123"}', headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert exp_ids == actual['sort_order']
        assert actual['resources']['123']['notation_style'] == 'https://cantus.org/notations/3895/'
        assert actual['resources']['123']['notation_style_id'] == '3895'

    @testing.gen_test
    def test_complicated_query(self):
        '''
        Works properly with a complicated query.

        There are:
        - some booleans in the search query
        - some grouping with ( ) in the search query
        - two subqueries, each with two results
        - two results to the main query, which are Source resources
        - those two results require looking up different cross-referenced fields
        '''
        # We need to make these available textually (for the subquery) and by ID (for the xref).
        # NOTE that by using the full "expected" call up here, we implicitly make an assertion about
        #      how Solr was called, so we don't need to check it later.
        # NOTE that we have to use "OR" in some of the queries, or else the xref queries interfere
        #      with the main query. That is, "id:829" matches both "id:829 OR id:757" and
        #      "century_id:829", so that "id:829" without the + sign will inadvertently return the
        #      century as part of the main query
        exp_century_call = 'century:  ( 20th  OR 21st  ) '
        self.solr.search_se.add(exp_century_call, {'type': 'century', 'id': '829', 'name': '20th century'})
        self.solr.search_se.add(exp_century_call, {'type': 'century', 'id': '830', 'name': '21st century'})
        self.solr.search_se.add('id:829 OR id:757', {'type': 'century', 'id': '829', 'name': '20th century'})
        self.solr.search_se.add('id:757 OR id:829', {'type': 'century', 'id': '829', 'name': '20th century'})
        self.solr.search_se.add('id:830 OR id:767', {'type': 'century', 'id': '830', 'name': '21st century'})
        self.solr.search_se.add('id:767 OR id:830', {'type': 'century', 'id': '830', 'name': '21st century'})
        #
        self.solr.search_se.add(
            'type:notation_style AND (square)',
            {'type': 'notation', 'id': '757', 'name': 'square notation'}
        )
        self.solr.search_se.add(
            'type:notation_style AND (triangle)',
            {'type': 'notation', 'id': '767', 'name': 'triangle notation'}
        )
        self.solr.search_se.add('id:829 OR id:757', {'type': 'notation', 'id': '757', 'name': 'square notation'})
        self.solr.search_se.add('id:757 OR id:829', {'type': 'notation', 'id': '757', 'name': 'square notation'})
        self.solr.search_se.add('id:830 OR id:767', {'type': 'notation', 'id': '767', 'name': 'triangle notation'})
        self.solr.search_se.add('id:767 OR id:830', {'type': 'notation', 'id': '767', 'name': 'triangle notation'})
        # for the "NOT"
        self.solr.search_se.add('19th', {'type': 'century', 'id': '800', 'name': '19th century'})
        # results of the main query itself
        self.solr.search_se.add('type:source', {'type': 'source', 'id': '4412', 'century_id': '829', 'notation_style_id': '757'})
        self.solr.search_se.add('type:source', {'type': 'source', 'id': '4413', 'century_id': '830', 'notation_style_id': '767'})
        #
        query = 'century:(20th OR 21st) && (notation_style:square OR notation_style:triangle) NOT century:19th'

        actual = yield self.http_client.fetch(self._browse_url,
                                              method='SEARCH',
                                              allow_nonstandard_methods=True,
                                              body=bytes('{{"query":"{}"}}'.format(query), encoding='utf-8'))

        self.check_standard_header(actual)
        # check how Solr was called for the main query
        self.solr.search.assert_any_call(
            'type:source  AND  ( (century_id:829 OR century_id:830)  &&  ( notation_style_id:757  OR notation_style_id:767  )  NOT century_id:800  ) ',
            df='default_search', rows=10)
        # check the right results were returned
        actual = escape.json_decode(actual.body)
        assert actual['sort_order'] == ['4412', '4413']
        for each_id in actual['sort_order']:
            assert 'self' in actual['resources'][each_id]
            assert 'century' in actual['resources'][each_id]
            assert 'notation_style' in actual['resources'][each_id]
            #
            assert 'id' in actual[each_id]
            assert 'type' in actual[each_id]
            assert 'century' in actual[each_id]
            assert 'notation_style' in actual[each_id]


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
