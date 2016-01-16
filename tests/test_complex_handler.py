#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_complex_handler.py
# Purpose:                Tests for the Abbot server's ComplexHandler.
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
Tests for the Abbot server's ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock
from tornado import httpclient, testing
from abbot import __main__ as main
from abbot import complex_handler
ComplexHandler = complex_handler.ComplexHandler
import shared


class TestLookUpXrefs(shared.TestHandler):
    '''
    Tests for the ComplexHandler.look_up_xrefs().
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestLookUpXrefs, self).setUp()
        self.solr = self.setUpSolr()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = ComplexHandler(self.get_app(), request, type_name='source',
                                      additional_fields=['title', 'rism', 'siglum',
                                                         'provenance_id', 'date', 'century_id',
                                                         'notation_style_id', 'segment_id',
                                                         'source_status_id', 'summary',
                                                         'liturgical_occasions', 'description',
                                                         'indexing_notes', 'indexing_date',
                                                         'indexers', 'editors', 'proofreaders',
                                                         'provenance_detail'])

    @testing.gen_test
    def test_field_is_string_with_id(self):
        "when the xreffed field is a string with an id"
        record = {'id': '123656', 'provenance_id': '3624'}
        self.solr.search_se.add('id:3624', {'id': '3624', 'name': 'Klosterneuburg'})
        expected = ({'id': '123656', 'provenance': 'Klosterneuburg'},
                    {'provenance': 'https://cantus.org/provenances/3624/'})

        actual = yield self.handler.look_up_xrefs(record)

        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @testing.gen_test
    def test_field_is_list_of_string(self):
        "when the xreffed field is a list of strings"
        record = {'id': '123656', 'proofreaders': ['124104']}
        self.solr.search_se.add('id:124104', {'id': '124104', 'display_name': 'Debra Lacoste'})
        expected = ({'id': '123656', 'proofreaders': ['Debra Lacoste']},
                    {'proofreaders': ['https://cantus.org/indexers/124104/']})

        actual = yield self.handler.look_up_xrefs(record)

        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @testing.gen_test
    def test_field_not_found_1(self):
        "when the xreffed field is a string, but it's not found in Solr"
        record = {'id': '123656', 'provenance_id': '3624'}
        expected = ({'id': '123656'},
                    {})

        actual = yield self.handler.look_up_xrefs(record)

        self.solr.search.assert_called_with('+type:provenance +id:3624', df='default_search')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @testing.gen_test
    def test_field_not_found_2(self, ):
        "when the xreffed field is a list of strings, but nothing is ever found in Solr"
        record = {'id': '123656', 'proofreaders': ['124104']}
        expected = ({'id': '123656'},
                    {})

        actual = yield self.handler.look_up_xrefs(record)

        self.solr.search.assert_called_with('+type:indexer +id:124104', df='default_search')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @testing.gen_test
    def test_many_xreffed_fields(self):
        "with many xreffed fields"
        record = {'id': '123656', 'provenance_id': '3624', 'segment_id': '4063',
                  'proofreaders': ['124104'], 'source_status_id': '4212', 'century_id': '3841'}
        expected = ({'id': '123656', 'provenance': 'Klosterneuburg', 'segment': 'CANTUS Database',
                     'proofreaders': ['Debra Lacoste'], 'source_status': 'Published / Complete',
                     'century': '14th century'},
                    {'provenance': 'https://cantus.org/provenances/3624/',
                     'segment': 'https://cantus.org/segments/4063/',
                     'proofreaders': ['https://cantus.org/indexers/124104/'],
                     'source_status': 'https://cantus.org/statii/4212/',
                     'century': 'https://cantus.org/centuries/3841/'})
        self.solr.search_se.add('id:3624', {'id': '3624', 'name': 'Klosterneuburg'})
        self.solr.search_se.add('id:4063', {'id': '4063', 'name': 'CANTUS Database'})
        self.solr.search_se.add('id:124104', {'id': '124104', 'display_name': 'Debra Lacoste'})
        self.solr.search_se.add('id:4212', {'id': '4212', 'name': 'Published / Complete'})
        self.solr.search_se.add('id:3841', {'id': '3841', 'name': '14th century'})

        actual = yield self.handler.look_up_xrefs(record)

        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @testing.gen_test
    def test_no_xref_is_true(self):
        "when self.hparams['no_xref'] is True"
        record = {'id': '123656', 'provenance_id': '3624'}
        expected = ({'id': '123656', 'provenance_id': '3624'},
                    {'provenance': 'https://cantus.org/provenances/3624/'})
        self.handler.hparams['no_xref'] = True

        actual = yield self.handler.look_up_xrefs(record)

        assert 0 == self.solr.search.call_count
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_lookup_name_for_response_1(self):
        '''
        ComplexHandler._lookup_name_for_response()
        It's not actually look_up_xrefs() but it's related... sort of... I just didn't want to make
        a whole new TestCase for that one method that has two tests.

        This tests a field that isn't changed.
        '''
        in_val = 'regular_field'
        expected = 'regular_field'
        actual = self.handler._lookup_name_for_response(in_val)
        self.assertEqual(expected, actual)

    def test_lookup_name_for_response_2(self):
        '''
        ComplexHandler._lookup_name_for_response()
        It's not actually look_up_xrefs() but it's related... sort of... I just didn't want to make
        a whole new TestCase for that one method that has two tests.

        This tests a field that is changed.
        '''
        in_val = 'source_id'
        expected = 'source'
        actual = self.handler._lookup_name_for_response(in_val)
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_issue_96(self):
        '''
        This is a regression test for GitHub issue 96.

        In this issue, cross-references to Notation resources were found to be incorrect. This test
        is to guarantee that look_up_xrefs() uses the "type" member of the LOOKUP object.
        '''
        record = {'id': '123656', 'notation_style_id': '3895'}
        self.solr.search_se.add('id:3895', {'id': '3895', 'name': 'German - neumatic'})
        expected = ({'id': '123656', 'notation_style': 'German - neumatic'},
                    {'notation_style': 'https://cantus.org/notations/3895/'})

        actual = yield self.handler.look_up_xrefs(record)

        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])


class TestMakeExtraFields(shared.TestHandler):
    '''
    Tests for the ComplexHandler.make_extra_fields().
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestMakeExtraFields, self).setUp()
        self.solr = self.setUpSolr()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = ComplexHandler(self.get_app(), request, type_name='source',
                                      additional_fields=['title', 'rism', 'siglum',
                                                         'provenance_id', 'date', 'century_id',
                                                         'notation_style_id', 'segment_id',
                                                         'source_status_id', 'summary',
                                                         'liturgical_occasions', 'description',
                                                         'indexing_notes', 'indexing_date',
                                                         'indexers', 'editors', 'proofreaders',
                                                         'provenance_detail'])
    @testing.gen_test
    def test_both_things_to_lookup(self):
        "with both a feast_id and source_status_id to look up"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {'feast_desc': 'boiled goose and collard greens', 'source_status_desc': 'Ready'}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!

        self.solr.search_se.add('id:123', {'id': '123', 'description': 'boiled goose and collard greens'})
        self.solr.search_se.add('id:456', {'id': '456', 'description': 'Ready'})

        actual = yield self.handler.make_extra_fields(record, orig_record)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_both_things_but_return_nothing(self):
        "with both a feast_id and source_status_id to look up, but they both return nothing"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!

        actual = yield self.handler.make_extra_fields(record, orig_record)

        self.solr.search.assert_any_caled('+type:feast +id:123', df='default_search')
        self.solr.search.assert_any_caled('+type:source_status +id:456', df='default_search')
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_nothing_to_lookup(self):
        "with neither a feast_id nor a source_status_id to look up"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields = ['id']  # remove everything, so we get nothing back

        actual = yield self.handler.make_extra_fields(record, orig_record)

        assert 0 == self.solr.search.call_count
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_no_xref_is_true(self):
        "when self.hparams['no_xref'] is True"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!
        self.handler.hparams['no_xref'] = True

        actual = yield self.handler.make_extra_fields(record, orig_record)

        assert 0 == self.solr.search.call_count
        self.assertEqual(expected, actual)


class TestVerifyRequestHeaders(shared.TestHandler):
    '''
    Tests for the ComplexHandler.verify_request_headers().
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestVerifyRequestHeaders, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = ComplexHandler(self.get_app(), request, type_name='source')
        # the full "additional_fields" aren't important here

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    def test_template(self, mock_super_meth, **kwargs):
        '''
        Template for tests against SimpleHandler.verify_request_headers().

        Use these kwargs to set test variables:

        - mock_super_meth_return: return value of the mock installed on
            SimpleHandler.verify_request_headers() (default is True)
        - no_xref: value for the handler's "no_xref" instance variable (default is 'false')
        - exp_no_xref: expected value of the "no_xref" after the method executes (default is False)
        - is_browse_request: value for that argument to the method under test (default is True)
        - expected: the method's expected return value (default is True)
        - exp_send_error_count: how many calls to the mock installed on send_error() are expected
            (default is 0)
        '''

        def get_from_kwargs(key, val):
            "Return kwargs[key] if that will work, otherwise return 'val.'"
            if key in kwargs:
                return kwargs[key]
            else:
                return val

        mock_super_meth.return_value = get_from_kwargs('mock_super_meth_return', True)
        self.handler.hparams['no_xref'] = get_from_kwargs('no_xref', 'false')
        exp_no_xref = get_from_kwargs('exp_no_xref', False)
        is_browse_request = get_from_kwargs('is_browse_request', True)
        expected = get_from_kwargs('expected', True)
        exp_send_error_count = get_from_kwargs('exp_send_error_count', 0)
        mock_send_error = mock.Mock()
        self.handler.send_error = mock_send_error

        actual = self.handler.verify_request_headers(is_browse_request)

        self.assertEqual(expected, actual)
        self.assertEqual(exp_send_error_count, mock_send_error.call_count)
        mock_super_meth.assert_called_once_with(is_browse_request=is_browse_request)
        self.assertEqual(exp_no_xref, self.handler.hparams['no_xref'])

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    def test_when_other_header_invalid(self, mock_super_meth):
        '''
        When SimpleHandler.verify_request_headers() determines one of the headers is invalid.

        The header shouldn't be checked, send_error() shouldn't be called.
        '''
        self.test_template(mock_super_meth_return=False,
                           no_xref='switchboard',
                           exp_no_xref='switchboard',
                           expected=False)

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    def test_no_xref_true(self, mock_super_meth):
        '''
        When self.hparams['no_xref'] comes out as True
        '''
        self.test_template(no_xref='  trUE   ', exp_no_xref=True)

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    def test_no_xref_false(self, mock_super_meth):
        '''
        When self.hparams['no_xref'] comes out as False
        '''
        self.test_template(no_xref='FALSE ', exp_no_xref=False)

    @mock.patch('abbot.simple_handler.SimpleHandler.verify_request_headers')
    def test_no_xref_invalid(self, mock_super_meth):
        '''
        When SimpleHandler.verify_request_headers() determines one of the headers is invalid.

        The header shouldn't be checked, send_error() shouldn't be called.
        '''
        self.test_template(no_xref='switchboard',
                           exp_no_xref='switchboard',
                           expected=False,
                           exp_send_error_count=1)
        self.handler.send_error.assert_called_once_with(400, reason=complex_handler._INVALID_NO_XREF)


class TestGetHandler(shared.TestHandler):
    '''
    Tests for ComplexHandler.get_handler().
    '''

    def setUp(self):
        super(TestGetHandler, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = ComplexHandler(self.get_app(), request, type_name='source',
                                      additional_fields=['title', 'rism', 'siglum',
                                                         'provenance_id', 'date', 'century_id',
                                                         'notation_style_id', 'segment_id',
                                                         'source_status_id', 'summary',
                                                         'liturgical_occasions', 'description',
                                                         'indexing_notes', 'indexing_date',
                                                         'indexers', 'editors', 'proofreaders',
                                                         'provenance_detail'])

    @mock.patch('abbot.complex_handler.ComplexHandler.basic_get')
    @testing.gen_test
    def test_no_results(self, mock_basic):
        '''
        A request that returns no results from Solr.

        - it calls basic_get() with proper resource_id and query
        - when basic_get() returns (None, 0), it also returns (None, 0)
        '''
        mock_basic.return_value = shared.make_future((None, 0))
        resource_id = '123'
        query = 'what do?'

        actual = yield self.handler.get_handler(resource_id, query)

        assert actual == (None, 0)
        mock_basic.assert_called_with(resource_id=resource_id, query=query)

    @mock.patch('abbot.complex_handler.ComplexHandler.make_extra_fields')
    @mock.patch('abbot.complex_handler.ComplexHandler.look_up_xrefs')
    @mock.patch('abbot.complex_handler.ComplexHandler.basic_get')
    @testing.gen_test
    def test_normal_behaviour(self, mock_basic, mock_xrefs, mock_extra):
        '''
        A request that goes normally.

        - self.hparams['include_resources'] is False
        - output doesn't include "resources"
        - self.look_up_xrefs() is called with every record
        - self.make_extra_fields() is called with the output of look_up_xrefs()
        - a returned resource is whatever make_extra_fields() returns
        '''
        self.handler.hparams['include_resources'] = False
        mock_basic.return_value = shared.make_future(({
            '1': 'resource 1',
            '2': 'resource 2',
            '3': 'resource 3',
            'sort_order': ['1', '2', '3']
        }, 23))
        # returns like ('resource 1x', {})
        mock_xrefs.side_effect = lambda x: shared.make_future(('{}x'.format(x), {}))
        # returns lik 'resource 1xe'
        mock_extra.side_effect = lambda x, y: shared.make_future('{}e'.format(x))

        actual = yield self.handler.get_handler()

        assert actual[1] == 23
        actual = actual[0]
        assert len(actual) == 4
        assert actual['sort_order'] == ['1', '2', '3']
        assert 'resources' not in actual
        for each_id in actual['sort_order']:
            assert actual[each_id] == 'resource {}xe'.format(each_id)

    @mock.patch('abbot.complex_handler.ComplexHandler.make_extra_fields')
    @mock.patch('abbot.complex_handler.ComplexHandler.look_up_xrefs')
    @mock.patch('abbot.complex_handler.ComplexHandler.basic_get')
    @testing.gen_test
    def test_include_resources(self, mock_basic, mock_xrefs, mock_extra):
        '''
        A request that goes normally.

        - self.hparams['include_resources'] is True
        - output includes "resources"
        - each record has its URL in "resources"
        - cross-referenced fields also have URLs in "resources"
        '''
        self.handler.hparams['include_resources'] = True
        mock_basic.return_value = shared.make_future(({
            '1': 'resource 1',
            '2': 'resource 2',
            '3': 'resource 3',
            'sort_order': ['1', '2', '3'],
            'resources': {'1': {'self': '1'}, '2': {'self': '2'}, '3': {'self': '3'}},
        }, 23))
        # returns like ('resource 1x', {'a': 'b'})
        mock_xrefs.side_effect = lambda x: shared.make_future(('{}x'.format(x), {'a': 'b'}))
        # returns lik 'resource 1xe'
        mock_extra.side_effect = lambda x, y: shared.make_future('{}e'.format(x))

        actual = yield self.handler.get_handler()

        actual = actual[0]
        for each_id in ('1', '2', '3'):
            assert actual['resources'][each_id] == {'a': 'b', 'self': each_id}
