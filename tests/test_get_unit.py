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

from abbot.complex_handler import ComplexHandler
from abbot import simple_handler
from abbot.simple_handler import SimpleHandler
import shared


class TestBasicGetSimple(shared.TestHandler):
    '''
    Unit tests for the SimpleHandler.basic_get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def __init__(self, *args, **kwargs):
        '''
        If "self._complex" is False, run the tests with a SimpleHandler.
        If "self._complex" is True, run the tests with a ComplexHandler.
        '''
        super(TestBasicGetSimple, self).__init__(*args, **kwargs)
        self._complex = False

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestBasicGetSimple, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        if self._complex:
            self.handler = ComplexHandler(self.get_app(), request, type_name='century')
        else:
            self.handler = SimpleHandler(self.get_app(), request, type_name='century')
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_prep_and_run_1(self):
        '''
        Verify the preparation and query-running steps. Don't prepare/verify return values.

        - unspecified resource_id: it becomes '*'
        - self.hparams['page'] is defined: the appropriate "start" argument is used
        - self.hparams['sort'] is defined: the appropriate "sort" argument is used
        - ask_solr_by_id() is called (with proper start, rows, sort args)
        '''
        self.handler.hparams['page'] = 4
        self.handler.hparams['per_page'] = 5
        self.handler.hparams['sort'] = 'roar'

        yield self.handler.basic_get()

        self.solr.search.assert_called_with('+type:century +id:*', start=15, rows=5, sort='roar',
            df='default_search')

    @testing.gen_test
    def test_prep_and_run_2(self):
        '''
        Verify the preparation and query-running steps. Don't prepare/verify return values.

        - if resource_id ends with "/" it gets removed before sending to Solr
        - self.hparams['page'] is not defined; no "start" arg is given
        - ask_solr_by_id() is called (with proper start, rows, sort args)
        '''
        resource_id = '911/'

        yield self.handler.basic_get(resource_id=resource_id)

        self.solr.search.assert_called_with('+type:century +id:911', df='default_search')

    @testing.gen_test
    def test_prep_and_run_3(self):
        '''
        Verify the preparation and query-running steps. Don't prepare/verify return values.

        - there is a resource_id, but also a "query", so search_solr() is called
        '''
        resource_id = '911/'
        query = 'wonderful'

        yield self.handler.basic_get(resource_id=resource_id, query=query)

        self.solr.search.assert_called_with(query, df='default_search')

    @testing.gen_test
    def test_prep_and_run_4(self):
        '''
        Verify the preparation and query-running steps. Don't prepare/verify return values.

        - there is a resource_id, but also a "query", so search_solr() is called
        - same as test_prep_and_run_3() BUT adds page/per_page/sort arguments, to ensure they also
          make it through search_solr()
        '''
        self.handler.hparams['page'] = 4
        self.handler.hparams['per_page'] = 5
        self.handler.hparams['sort'] = 'roar'
        resource_id = '911/'
        query = 'wonderful'

        yield self.handler.basic_get(resource_id=resource_id, query=query)

        self.solr.search.assert_called_with(query, start=15, rows=5, sort='roar', df='default_search')

    @testing.gen_test
    def test_prep_and_run_5(self):
        '''
        Verify the preparation and query-running steps. Don't prepare/verify return values.

        - ask_solr_by_id() raises ValueError because of an invalid resource ID
        - basic_get() calls send_error(422, reason=_INVALID_ID)
        - function returns (None, 0) (yes, breaking the rules a bit)
        - make sure Solr is not called (or it could cause problems there)
        '''
        resource_id = '-911'
        self.handler.send_error = mock.Mock()

        yield self.handler.basic_get(resource_id=resource_id)

        assert 0 == self.solr.search.call_count
        self.handler.send_error.assert_called_once_with(422, reason=simple_handler._INVALID_ID)

    @mock.patch('abbot.simple_handler.util.search_solr')
    @testing.gen_test
    def test_no_results_1(self, mock_solr):
        '''
        Verify behaviour when Solr returns no results.

        - if X-Cantus-Page is too high (this is determined when the "start" argument to Solr is
          greater than the "hits" Solr reports for that query
        - send 409 with _TOO_LARGE_PAGE
        - return (None, 0)
        '''
        self.handler.hparams['page'] = 99999
        self.handler.hparams['per_page'] = 5
        self.handler.send_error = mock.Mock()
        expected = (None, 0)
        # this test requires something very specific, so we'll mock Solr ourselves
        results = shared.make_results([])
        results.hits = 4000
        mock_solr.return_value = shared.make_future(results)

        actual = yield self.handler.basic_get(query='whatever')

        assert actual == expected
        self.handler.send_error.assert_called_once_with(409, reason=simple_handler._TOO_LARGE_PAGE)

    @testing.gen_test
    def test_no_results_2(self):
        '''
        Verify behaviour when Solr returns no results.

        - there's a "query"
        - send 404 with _NO_SEARCH_RESULTS
        - return (None, 0)
        '''
        query = 'Vasco da Gama'
        self.handler.send_error = mock.Mock()
        expected = (None, 0)

        actual = yield self.handler.basic_get(query=query)

        assert actual == expected
        self.handler.send_error.assert_called_once_with(404, reason=simple_handler._NO_SEARCH_RESULTS)

    @testing.gen_test
    def test_no_results_3(self):
        '''
        Verify behaviour when Solr returns no results.

        - there's a resource_id
        - send 404 with _ID_NOT_FOUND
        - return (None, 0)
        '''
        resource_id = '48839929'
        self.handler.send_error = mock.Mock()
        expected = (None, 0)
        exp_reason = simple_handler._ID_NOT_FOUND.format('century', resource_id)

        actual = yield self.handler.basic_get(resource_id=resource_id)

        assert actual == expected
        self.handler.send_error.assert_called_once_with(404, reason=exp_reason)

    @testing.gen_test
    def test_with_results_1(self):
        '''
        Verify behaviour when Solr does give results.

        - call self.format_record() on each of the rescords
        - verify "number_of_records" is correct (it's returned)
        - verify "sort_order" is the same order as records in the response (it's in returned response)
        - verify the "self.total_results" was set to the "hits" from the response
        '''
        self.solr.search_se.add('*', {'id': '6', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '9', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'type': 'century'})
        exp_num_records = 3
        exp_sort_order = ['6', '9', '2']
        exp_total_results = 3

        actual = yield self.handler.basic_get()

        assert exp_num_records == actual[1]
        assert self.handler.total_results == exp_total_results
        assert exp_sort_order == actual[0]['sort_order']
        for each_id in exp_sort_order:
            assert actual[0][each_id]['id'] == each_id
            assert actual[0][each_id]['type'] == 'century'

    @testing.gen_test
    def test_with_results_2(self):
        '''
        Verify behaviour when Solr does give results.

        - self.hparams['include_resources'] is True
        - each resource has its URL put in a "resources" block
        '''
        self.handler.hparams['include_resources'] = True
        self.solr.search_se.add('*', {'id': '6', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '9', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'type': 'century'})
        exp_ids = ['2', '6', '9']
        exp_urls = ['{0}centuries/{1}/'.format(self._simple_options.server_name, x) for x in exp_ids]

        actual = yield self.handler.basic_get()
        actual = actual[0]

        for i, each_id in enumerate(exp_ids):
            assert actual['resources'][each_id]['self'] == exp_urls[i]

    @testing.gen_test
    def test_with_results_3(self):
        '''
        Verify behaviour when Solr does give results.

        - there's a Drupal URL available
        - each resource has a "drupal_path" member in its resource
        '''
        self.handler.hparams['include_resources'] = True
        self._simple_options.drupal_url = 'http://drupal/'
        self.solr.search_se.add('*', {'id': '6', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '9', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'type': 'century'})
        exp_ids = ['2', '6', '9']
        exp_urls = ['{0}century/{1}'.format(self._simple_options.drupal_url, x) for x in exp_ids]

        actual = yield self.handler.basic_get()
        actual = actual[0]

        for i, each_id in enumerate(exp_ids):
            assert actual[each_id]['drupal_path'] == exp_urls[i]


class TestGetSimple(shared.TestHandler):
    '''
    Unit tests for the SimpleHandler.get() and SimpleHandler.get_handler().
    '''

    def __init__(self, *args, **kwargs):
        '''
        If "self._complex" is False, run the tests with a SimpleHandler.
        If "self._complex" is True, run the tests with a ComplexHandler.
        '''
        super(TestGetSimple, self).__init__(*args, **kwargs)
        self._complex = False

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestGetSimple, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        if self._complex:
            self.handler = ComplexHandler(self.get_app(), request, type_name='century')
        else:
            self.handler = SimpleHandler(self.get_app(), request, type_name='century')
        # mocks specific to this class
        self.mock_vrh = mock.Mock(return_value=True)
        self.handler.verify_request_headers = self.mock_vrh
        #
        self.mock_ghandler = mock.Mock(return_value=(None, 0))
        self.handler.get_handler = self.mock_ghandler
        #
        self.mock_mrh = mock.Mock()
        self.handler.make_response_headers = self.mock_mrh

    @testing.gen_test
    def test_calls_vrh(self):
        '''
        Ensure get() calls verify_request_headers() (or "vrh").

        - two calls in the same test, expecting different values for "is_browse_request"
        - also check get_handler() won't be called when "vrh" returns False
        '''
        self.mock_vrh.return_value = False
        #
        yield self.handler.get('not a browse request')
        self.mock_vrh.assert_called_with(False)
        #
        yield self.handler.get()
        self.mock_vrh.assert_called_with(True)
        #
        assert self.mock_ghandler.call_count == 0

    @testing.gen_test
    def test_no_results(self):
        '''
        When get_handler() returns (None, 0) there was a problem getting results.

        - get_handler() returns (None, 0)
        - make_response_headers() isn't called
        '''
        yield self.handler.get()
        assert self.mock_ghandler.call_count == 1
        assert self.mock_mrh.call_count == 0

    @testing.gen_test
    def test_solr_error(self):
        '''
        When there's a SolrError.

        - get_handler() raises SolrError
        - make_response_headers() isn't called
        '''
        self.handler.send_error = mock.Mock()
        self.mock_ghandler.side_effect = pysolrtornado.SolrError
        yield self.handler.get()
        assert self.mock_ghandler.call_count == 1
        assert self.mock_mrh.call_count == 0
        self.handler.send_error.assert_called_with(502, reason=simple_handler._SOLR_502_ERROR)

    @testing.gen_test
    def test_works_not_head(self):
        '''
        When the Solr request is successful, and this is not a HEAD request.

        - get_handler() returns something good
        - make_response_headers() is called properly
        - self.write() is called
        '''
        self.handler.head_request = False
        self.handler.write = mock.Mock()
        self.mock_ghandler.return_value = shared.make_future(('yo', 5))
        yield self.handler.get()
        self.mock_mrh.assert_called_with(True, 5)
        self.handler.write.assert_called_with('yo')

    @testing.gen_test
    def test_works_is_head(self):
        '''
        When the Solr request is successful, and this is a HEAD request.

        - get_handler() returns something good
        - make_response_headers() is called properly
        - self.write() is called
        '''
        self.handler.head_request = True
        self.handler.write = mock.Mock()
        self.mock_ghandler.return_value = shared.make_future(('yo', 5))
        yield self.handler.get()
        self.mock_mrh.assert_called_with(True, 5)
        assert self.handler.write.call_count == 0


class TestBasicGetComplex(TestBasicGetSimple):
    '''
    Run all the TestBasicGetSimple unit tests with a ComplexHandler instead.

    Because basic_get() should behave identically for SimpleHandler and ComplexHandler, copying all
    the tests would be a worse solution. This way, differences between the two handlers should be
    easier to run into accidentally.
    '''

    def __init__(self, *args, **kwargs):
        "Set self._complex to True."
        super(TestBasicGetComplex, self).__init__(*args, **kwargs)
        self._complex = True


class TestGetComplex(TestGetSimple):
    '''
    Run all the TestGetSimple unit tests with a ComplexHandler instead.

    Because get() should behave identically for SimpleHandler and ComplexHandler, copying all
    the tests would be a worse solution. This way, differences between the two handlers should be
    easier to run into accidentally.
    '''

    def __init__(self, *args, **kwargs):
        "Set self._complex to True."
        super(TestGetComplex, self).__init__(*args, **kwargs)
        self._complex = True
