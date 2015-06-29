#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_complex_handler.py
# Purpose:                Tests for the Abbott server's ComplexHandler.
#
# Copyright (C) 2015 Christopher Antila
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
Tests for the Abbott server's ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock
from tornado import escape, httpclient, testing
from abbott import __main__ as main
from abbott.complex_handler import ComplexHandler
import shared


class TestLookUpXrefs(shared.TestHandler):
    '''
    Tests for the ComplexHandler.look_up_xrefs().
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestLookUpXrefs, self).setUp()
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

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_field_is_string_with_id(self, mock_ask_solr):
        "when the xreffed field is a string with an id"
        record = {'id': '123656', 'provenance_id': '3624'}
        mock_solr_response = [{'id': '3624', 'name': 'Klosterneuburg'}]
        expected = ({'id': '123656', 'provenance': 'Klosterneuburg'},
                    {'provenance': '/provenances/3624/'})
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('provenance', '3624')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_field_is_list_of_string(self, mock_ask_solr):
        "when the xreffed field is a list of strings"
        record = {'id': '123656', 'proofreaders': ['124104']}
        mock_solr_response = [{'id': '124104', 'display_name': 'Debra Lacoste'}]
        expected = ({'id': '123656', 'proofreaders': ['Debra Lacoste']},
                    {'proofreaders': ['/indexers/124104/']})
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('indexer', '124104')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_field_not_found_1(self, mock_ask_solr):
        "when the xreffed field is a string, but it's not found in Solr"
        record = {'id': '123656', 'provenance_id': '3624'}
        mock_solr_response = []
        expected = ({'id': '123656'},
                    {})
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('provenance', '3624')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_field_not_found_2(self, mock_ask_solr):
        "when the xreffed field is a list of strings, but nothing is ever found in Solr"
        record = {'id': '123656', 'proofreaders': ['124104']}
        mock_solr_response = [{}]
        expected = ({'id': '123656'},
                    {})
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('indexer', '124104')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_many_xreffed_fields(self, mock_ask_solr):
        "with many xreffed fields"
        record = {'id': '123656', 'provenance_id': '3624', 'segment_id': '4063',
                  'proofreaders': ['124104'], 'source_status_id': '4212', 'century_id': '3841'}
        expected = ({'id': '123656', 'provenance': 'Klosterneuburg', 'segment': 'CANTUS Database',
                     'proofreaders': ['Debra Lacoste'], 'source_status': 'Published / Complete',
                     'century': '14th century'},
                    {'provenance': '/provenances/3624/', 'segment': '/segments/4063/',
                     'proofreaders': ['/indexers/124104/'], 'source_status': '/statii/4212/',
                     'century': '/centuries/3841/'})

        def fake_solr(q_type, q_id):  # pylint: disable=unused-argument
            "mock version of ask_solr_by_id()"
            records = {'3624': [{'id': '3624', 'name': 'Klosterneuburg'}],
                       '4063': [{'id': '4063', 'name': 'CANTUS Database'}],
                       '124104': [{'id': '124104', 'display_name': 'Debra Lacoste'}],
                       '4212': [{'id': '4212', 'name': 'Published / Complete'}],
                       '3841': [{'id': '3841', 'name': '14th century'}],
                      }
            return shared.make_future(records[q_id])
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_any_call('provenance', '3624')
        mock_ask_solr.assert_any_call('segment', '4063')
        mock_ask_solr.assert_any_call('indexer', '124104')
        mock_ask_solr.assert_any_call('source_status', '4212')
        mock_ask_solr.assert_any_call('century', '3841')
        # etc.
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_no_xref_is_true(self, mock_ask_solr):
        "when self.no_xref is True"
        record = {'id': '123656', 'provenance_id': '3624'}
        mock_solr_response = [{'id': '3624', 'name': 'Klosterneuburg'}]
        expected = ({'id': '123656', 'provenance_id': '3624'},
                    {'provenance': '/provenances/3624/'})
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.no_xref = True

        actual = yield self.handler.look_up_xrefs(record)

        self.assertEqual(0, mock_ask_solr.call_count)
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


class TestMakeExtraFields(shared.TestHandler):
    '''
    Tests for the ComplexHandler.make_extra_fields().
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestMakeExtraFields, self).setUp()
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
    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_both_things_to_lookup(self, mock_ask_solr):
        "with both a feast_id and source_status_id to look up"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {'feast_desc': 'boiled goose and collard greens', 'source_status_desc': 'Ready'}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!

        def fake_solr(q_type, q_id):  # pylint: disable=unused-argument
            "mock version of ask_solr_by_id()"
            records = {'123': [{'id': '123', 'description': 'boiled goose and collard greens'}],
                       '456': [{'id': '456', 'description': 'Ready'}],
                      }
            return shared.make_future(records[q_id])
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.handler.make_extra_fields(record, orig_record)

        mock_ask_solr.assert_any_call('feast', '123')
        mock_ask_solr.assert_any_call('source_status', '456')
        # etc.
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_both_things_but_return_nothing(self, mock_ask_solr):
        "with both a feast_id and source_status_id to look up, but they both return nothing"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!

        def fake_solr(q_type, q_id):  # pylint: disable=unused-argument
            "mock version of ask_solr_by_id()"
            return shared.make_future({})
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.handler.make_extra_fields(record, orig_record)

        mock_ask_solr.assert_any_call('feast', '123')
        mock_ask_solr.assert_any_call('source_status', '456')
        # etc.
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_nothing_to_lookup(self, mock_ask_solr):
        "with neither a feast_id nor a source_status_id to look up"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields = ['id']  # remove everything, so we get nothing back

        def fake_solr(q_type, q_id):  # pylint: disable=unused-argument
            "mock version of ask_solr_by_id()"
            return shared.make_future({})
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.handler.make_extra_fields(record, orig_record)

        self.assertEqual(0, mock_ask_solr.call_count)
        # etc.
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_no_xref_is_true(self, mock_ask_solr):
        "when self.no_xref is True"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!
        self.handler.no_xref = True

        actual = yield self.handler.make_extra_fields(record, orig_record)

        self.assertEqual(0, mock_ask_solr.call_count)
        # etc.
        self.assertEqual(expected, actual)


class TestGetIntegration(shared.TestHandler):
    '''
    Unit tests for the ComplexHandler.get().
    '''

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_1(self, mock_ask_solr):
        "With many xreffed fields; feast_description to make up; and include 'resources'"
        record = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                  'mode': '2S'}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre': 'Responsory Verse',
                               'cantus_id': '600482a', 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'},
                    'resources': {'357679': {'self': '/chants/357679/', 'genre': '/genres/161/',
                                             'feast': '/feasts/2378/'}}}

        def fake_solr(q_type, q_id, **kwargs):  # pylint: disable=unused-argument
            "mock version of ask_solr_by_id()"
            records = {'357679': [record],
                       '161': [{'name': 'V', 'description': 'Responsory Verse'}],
                       '600482a': [],  # empty until we decide on fill_from_cantusid()
                       '2378': [{'name': 'Jacobi', 'description': 'James the Greater, Aspotle'}],
                      }
            return shared.make_future(shared.make_results(records[q_id]))
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.http_client.fetch(self.get_url('/chants/357679/'), method='GET')

        self.check_standard_header(actual)
        mock_ask_solr.assert_any_call('chant', '357679')
        mock_ask_solr.assert_any_call('genre', '161')
        mock_ask_solr.assert_any_call('feast', '2378')
        # right now, the "cantusid" won't be looked up unless "feast_id" is missing
        self.assertEqual(expected, escape.json_decode(actual.body))
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'].lower())

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_2(self, mock_ask_solr):
        "for the X-Cantus-Fields and X-Cantus-Extra-Fields headers; and with multiple returns"
        record_a = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                    'mode': '2S'}
        record_b = {'id': '111222', 'genre_id': '161', 'feast_id': '2378', 'mode': '2S',
                    'sequence': 4}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre': 'Responsory Verse',
                               'cantus_id': '600482a', 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'},
                    '111222': {'id': '111222', 'type': 'chant', 'genre': 'Responsory Verse',
                               'sequence': 4, 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'}}

        def fake_solr(q_type, q_id, **kwargs):  # pylint: disable=unused-argument
            "mock version of ask_solr_by_id()"
            records = {'*': [record_a, record_b],
                       '161': [{'name': 'V', 'description': 'Responsory Verse'}],
                       '600482a': [],  # empty until we decide on fill_from_cantusid()
                       '2378': [{'name': 'Jacobi', 'description': 'James the Greater, Aspotle'}],
                      }
            return shared.make_future(shared.make_results(records[q_id]))
        mock_ask_solr.side_effect = fake_solr
        # expected header: X-Cantus-Fields
        exp_cantus_fields = sorted(['id', 'genre', 'mode', 'feast', 'type'])
        # expected header: X-Cantus-Extra-Fields
        exp_extra_fields = sorted(['cantus_id', 'sequence'])

        actual = yield self.http_client.fetch(self.get_url('/chants/'),
                                              method='GET',
                                              headers={'X-Cantus-Include-Resources': 'FalSE'})

        self.assertEqual(exp_cantus_fields, sorted(actual.headers['X-Cantus-Fields'].split(',')))
        self.assertEqual(exp_extra_fields, sorted(actual.headers['X-Cantus-Extra-Fields'].split(',')))
        self.assertEqual('false', actual.headers['X-Cantus-Include-Resources'].lower())
        self.assertEqual(expected, escape.json_decode(actual.body))

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_3(self, mock_ask_solr):
        "test_get_integration_1 but with X-Cantus-No-Xref; include 'resources'"
        record = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                  'mode': '2S'}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre_id': '161',
                               'cantus_id': '600482a', 'feast_id': '2378', 'mode': '2S'},
                    'resources': {'357679': {'self': '/chants/357679/', 'genre': '/genres/161/',
                                             'feast': '/feasts/2378/'}}}

        def fake_solr(q_type, q_id, **kwargs):  # pylint: disable=unused-argument
            "mock version of ask_solr_by_id()"
            records = {'357679': [record]}
            return shared.make_future(shared.make_results(records[q_id]))
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.http_client.fetch(self.get_url('/chants/357679/'),
                                              method='GET',
                                              headers={'X-Cantus-No-Xref': 'TRUE'})

        self.check_standard_header(actual)
        mock_ask_solr.assert_called_once_with('chant', '357679')
        # right now, the "cantusid" won't be looked up unless "feast_id" is missing
        self.assertEqual(expected, escape.json_decode(actual.body))
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'].lower())
        self.assertEqual('true', actual.headers['X-Cantus-No-Xref'].lower())


class TestOptionsIntegration(shared.TestHandler):
    '''
    Integration tests for the ComplexHandler.options().
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestOptionsIntegration, self).setUp()
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
    def test_options_integration_1(self):
        "ensure the OPTIONS method works as expected ('browse' URL)"
        # adds X-Cantus-No-Xref over the SimpleHandler tests
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-No-Xref',
                            'X-Cantus-Per-Page', 'X-Cantus-Page', 'X-Cantus-Sort',
                            'X-Cantus-Search-Help']
        actual = yield self.http_client.fetch(self.get_url('/chants/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual('GET, HEAD, OPTIONS, SEARCH', actual.headers['Allow'])
        self.assertEqual('GET, HEAD, OPTIONS, SEARCH', actual.headers['Access-Control-Allow-Methods'])
        self.assertEqual(0, len(actual.body))
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_options_integration_2(self, mock_ask_solr):
        "ensure the OPTIONS method works as expected ('view' URL)"
        # adds X-Cantus-No-Xref over the SimpleHandler tests
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-No-Xref']
        mock_solr_response = shared.make_results(['Versicle'])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        actual = yield self.http_client.fetch(self.get_url('/chants/432/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual('GET, HEAD, OPTIONS', actual.headers['Allow'])
        self.assertEqual('GET, HEAD, OPTIONS', actual.headers['Access-Control-Allow-Methods'])
        self.assertEqual(0, len(actual.body))
        mock_ask_solr.assert_called_once_with('chant', '432')
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())


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

    @mock.patch('abbott.simple_handler.SimpleHandler.verify_request_headers')
    def test_when_other_header_invalid(self, mock_super_meth):
        '''
        When SimpleHandler.verify_request_headers() determines one of the headers is invalid.

        The header shouldn't be checked, send_error() shouldn't be called.
        '''
        mock_super_meth.return_value = False
        mock_send_error = mock.Mock()
        self.handler.send_error = mock_send_error
        self.handler.no_xref = 'switchboard'
        exp_no_xref = 'switchboard'
        is_browse_request = True
        expected = False

        actual = self.handler.verify_request_headers(is_browse_request)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mock_send_error.call_count)
        mock_super_meth.assert_called_once_with(is_browse_request=is_browse_request)
        self.assertEqual(exp_no_xref, self.handler.no_xref)

    @mock.patch('abbott.simple_handler.SimpleHandler.verify_request_headers')
    def test_no_xref_true(self, mock_super_meth):
        '''
        When self.no_xref comes out as True
        '''
        mock_super_meth.return_value = True
        mock_send_error = mock.Mock()
        self.handler.send_error = mock_send_error
        self.handler.no_xref = ' trUE   '
        exp_no_xref = True
        is_browse_request = True
        expected = True

        actual = self.handler.verify_request_headers(is_browse_request)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mock_send_error.call_count)
        mock_super_meth.assert_called_once_with(is_browse_request=is_browse_request)
        self.assertEqual(exp_no_xref, self.handler.no_xref)

    @mock.patch('abbott.simple_handler.SimpleHandler.verify_request_headers')
    def test_no_xref_false(self, mock_super_meth):
        '''
        When self.no_xref comes out as False
        '''
        mock_super_meth.return_value = True
        mock_send_error = mock.Mock()
        self.handler.send_error = mock_send_error
        self.handler.no_xref = 'FALSE '
        exp_no_xref = False
        is_browse_request = True
        expected = True

        actual = self.handler.verify_request_headers(is_browse_request)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mock_send_error.call_count)
        mock_super_meth.assert_called_once_with(is_browse_request=is_browse_request)
        self.assertEqual(exp_no_xref, self.handler.no_xref)

    @mock.patch('abbott.simple_handler.SimpleHandler.verify_request_headers')
    def test_no_xref_invalid(self, mock_super_meth):
        '''
        When SimpleHandler.verify_request_headers() determines one of the headers is invalid.

        The header shouldn't be checked, send_error() shouldn't be called.
        '''
        mock_super_meth.return_value = True
        mock_send_error = mock.Mock()
        self.handler.send_error = mock_send_error
        self.handler.no_xref = 'switchboard'
        is_browse_request = True
        expected = False

        actual = self.handler.verify_request_headers(is_browse_request)

        self.assertEqual(expected, actual)
        mock_send_error.assert_called_once_with(400, reason=ComplexHandler._INVALID_NO_XREF)
        mock_super_meth.assert_called_once_with(is_browse_request=is_browse_request)
