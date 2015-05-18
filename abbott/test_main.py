#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/test_main.py
# Purpose:                Tests for __main__.py of the Abbott server.
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
Tests for ``__main__.py`` of the Abbott server.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

import unittest
from unittest import mock
from tornado import concurrent, escape, httpclient, testing, web
import pysolrtornado
from abbott import __main__ as main


def make_future(with_this):
    '''
    Creates a new :class:`Future` with the function's argument as the result.
    '''
    val = concurrent.Future()
    val.set_result(with_this)
    return val


class TestHandler(testing.AsyncHTTPTestCase):
    "Base class for classes that test a ___Handler."
    def get_app(self):
        return web.Application(main.HANDLERS)

    def check_standard_header(self, on_this):
        '''
        Verify the proper values for the headers that should be part of every response, Server and
        X-Cantus-Version.

        :param on_this: The :class:`Response` object to verify.
        :type on_this: :class:`tornado.httpclient.HTTPResponse`
        '''
        self.assertEqual('Abbott/{}'.format(main.ABBOTT_VERSION), on_this.headers['Server'])
        self.assertEqual('Cantus/{}'.format(main.CANTUS_API_VERSION), on_this.headers['X-Cantus-Version'])


class TestAbbott(TestHandler):
    '''
    Tests for module-level things.
    '''

    def test_singular_resource_to_plural_1(self):
        "When the singular form has a corresponding pural."
        self.assertEqual('cantusids', main.singular_resource_to_plural('cantusid'))

    def test_singular_resource_to_plural_2(self):
        "When the singular form doesn't have a corresponding plural."
        self.assertIsNone(main.singular_resource_to_plural('automobiles'))

    @mock.patch('abbott.__main__.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_ask_solr_by_id_1(self, mock_solr):
        "Basic test."
        mock_solr.search.return_value = make_future('search results')
        expected = 'search results'
        actual = yield main.ask_solr_by_id('genre', '162')
        self.assertEqual(expected, actual)
        main.SOLR.search.assert_called_once_with('+type:genre +id:162')

    @mock.patch('abbott.__main__.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_ask_solr_by_id_2(self, mock_solr):
        "with 'start' and 'rows' kwargs"
        mock_solr.search.return_value = make_future('search results')
        expected = 'search results'
        actual = yield main.ask_solr_by_id('genre', '162', start=5, rows=50)
        self.assertEqual(expected, actual)
        main.SOLR.search.assert_called_once_with('+type:genre +id:162', start=5, rows=50)

    @mock.patch('abbott.__main__.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_ask_solr_by_id_3(self, mock_solr):
        "with 'rows' and 'sort' kwargs"
        mock_solr.search.return_value = make_future('search results')
        expected = 'search results'
        actual = yield main.ask_solr_by_id('genre', '162', rows=42, sort='incipit asc')
        self.assertEqual(expected, actual)
        main.SOLR.search.assert_called_once_with('+type:genre +id:162', rows=42, sort='incipit asc')


class TestRootHandler(TestHandler):
    '''
    Tests for the RootHandler.
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestRootHandler, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = main.RootHandler(self.get_app(), request)

    def test_root_1(self):
        "basic test"
        all_plural_resources = [
            'cantusids',
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
        expected = {'browse_{}'.format(term): '/{}/id?'.format(term) for term in all_plural_resources}
        expected['browse_source_statii'] = '/statii/id?'
        expected = {'resources': expected}

        actual = self.handler.prepare_get()

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_root_2(self):
        "integration test for test_root_1()"
        all_plural_resources = [
            'cantusids',
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
        expected = {'browse_{}'.format(term): '/{}/id?'.format(term) for term in all_plural_resources}
        expected['browse_source_statii'] = '/statii/id?'
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
        self.assertEqual(main.RootHandler._ALLOWED_METHODS, actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))


class TestSimpleHandler(TestHandler):
    '''
    Tests for the SimpleHandler.

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSimpleHandler, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = main.SimpleHandler(self.get_app(), request, type_name='century')

    def test_initialize_1(self):
        "initialize() works with no extra fields"
        self.assertEqual('century', self.handler.type_name)
        self.assertEqual('centuries', self.handler.type_name_plural)
        self.assertEqual(4, len(self.handler.returned_fields))

    def test_initialize_2(self):
        "initialize() works with extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET', headers={'X-Cantus-Include-Resources': 'TRue'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = main.SimpleHandler(self.get_app(), request, type_name='genre', additional_fields=['mass_or_office'])
        self.assertEqual('genre', actual.type_name)
        self.assertEqual('genres', actual.type_name_plural)
        self.assertEqual(5, len(actual.returned_fields))
        self.assertTrue('mass_or_office' in actual.returned_fields)
        self.assertTrue(actual.include_resources)

    def test_initialize_2(self):
        "initialize() works with extra fields (different values)"
        request = httpclient.HTTPRequest(url='/zool/', method='GET', headers={'X-Cantus-Include-Resources': 'fALSe'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = main.SimpleHandler(self.get_app(), request, type_name='twist')
        self.assertFalse(actual.include_resources)

    def test_format_record_1(self):
        "basic test"
        input_record = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}
        input_record['false advertising'] = 'not allowed'  # this key obviously should never appear "for real"
        expected = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}

        actual = self.handler.format_record(input_record)

        self.assertEqual(expected, actual)
        # ensure fields were counted properly
        self.assertEqual(len(self.handler.returned_fields), len(self.handler.field_counts))
        for field in self.handler.returned_fields:
            self.assertEqual(1, self.handler.field_counts[field])

    def test_make_resource_url_1(self):
        "with no resource_type specified"
        expected = '/centuries/420/'
        actual = self.handler.make_resource_url('420')
        self.assertEqual(expected, actual)

    def test_make_resource_url_2(self):
        "with singuler resource_type"
        expected = '/chants/69/'
        actual = self.handler.make_resource_url('69', 'chant')
        self.assertEqual(expected, actual)

    def test_make_resource_url_3(self):
        "with plural resource_type"
        expected = '/sources/3.14159/'
        actual = self.handler.make_resource_url('3.14159', 'sources')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_1(self, mock_ask_solr):
        "with no resource_id and Solr response has three things"
        resource_id = None
        mock_solr_response = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_2(self, mock_ask_solr):
        "with resource_id ending in '/' Solr response is empty"
        resource_id = '123/'
        mock_solr_response = []
        expected = {'resources': {}}
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '123')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_3(self, mock_ask_solr):
        "with resource_id not ending with '/' and Solr response has one thing"
        resource_id = '888'  # such good luck
        mock_solr_response = [{'id': '888'}]
        expected = {'888': {'id': '888', 'type': 'century'}, 'resources': {'888': {'self': '/centuries/888/'}}}
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '888')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_4(self, mock_ask_solr):
        "test_basic_get_unit_1() with self.include_resources set to False"
        resource_id = None
        mock_solr_response = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'}}
        mock_ask_solr.return_value = make_future(mock_solr_response)

        self.handler.include_resources = False
        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_1(self, mock_ask_solr):
        "test_basic_get_unit_1() but through the whole App infrastructure (thus using get())"
        mock_solr_response = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET')

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*')
        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_options_integration_1(self):
        "ensure the OPTIONS method works as expected"
        actual = yield self.http_client.fetch(self.get_url('/genres/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual(main.SimpleHandler._ALLOWED_METHODS, actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))


class TestComplexHandler(TestHandler):
    '''
    Tests for the ComplexHandler.
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestComplexHandler, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = main.ComplexHandler(self.get_app(), request, type_name='source',
                                           additional_fields=['title', 'rism', 'siglum',
                                                              'provenance_id', 'date', 'century_id',
                                                              'notation_style_id', 'segment_id',
                                                              'source_status_id', 'summary',
                                                              'liturgical_occasions', 'description',
                                                              'indexing_notes', 'indexing_date',
                                                              'indexers', 'editors', 'proofreaders',
                                                              'provenance_detail'])

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_look_up_xrefs_unit_1(self, mock_ask_solr):
        "when the xreffed field is a string with an id"
        record = {'id': '123656', 'provenance_id': '3624'}
        mock_solr_response = [{'id': '3624', 'name': 'Klosterneuburg'}]
        expected = ({'id': '123656', 'provenance': 'Klosterneuburg'},
                    {'provenance': '/provenances/3624/'})
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('provenance', '3624')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_look_up_xrefs_unit_2(self, mock_ask_solr):
        "when the xreffed field is a list of strings"
        record = {'id': '123656', 'proofreaders': ['124104']}
        mock_solr_response = [{'id': '124104', 'display_name': 'Debra Lacoste'}]
        expected = ({'id': '123656', 'proofreaders': ['Debra Lacoste']},
                    {'proofreaders': ['/indexers/124104/']})
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('indexer', '124104')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_look_up_xrefs_unit_3(self, mock_ask_solr):
        "when the xreffed field is a string, but it's not found in Solr"
        record = {'id': '123656', 'provenance_id': '3624'}
        mock_solr_response = []
        expected = ({'id': '123656'},
                    {})
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('provenance', '3624')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_look_up_xrefs_unit_4(self, mock_ask_solr):
        "when the xreffed field is a list of strings, but nothing is ever found in Solr"
        record = {'id': '123656', 'proofreaders': ['124104']}
        mock_solr_response = [{}]
        expected = ({'id': '123656'},
                    {})
        mock_ask_solr.return_value = make_future(mock_solr_response)

        actual = yield self.handler.look_up_xrefs(record)

        mock_ask_solr.assert_called_once_with('indexer', '124104')
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_look_up_xrefs_unit_5(self, mock_ask_solr):
        "with many xreffed fields"
        record = {'id': '123656', 'provenance_id': '3624', 'segment_id': '4063',
                  'proofreaders': ['124104'], 'source_status_id': '4212', 'century_id': '3841'}
        expected = ({'id': '123656', 'provenance': 'Klosterneuburg', 'segment': 'CANTUS Database',
                     'proofreaders': ['Debra Lacoste'], 'source_status': 'Published / Complete',
                     'century': '14th century'},
                    {'provenance': '/provenances/3624/', 'segment': '/segments/4063/',
                     'proofreaders': ['/indexers/124104/'], 'source_status': '/statii/4212/',
                     'century': '/centuries/3841/'})

        def fake_solr(q_type, q_id):
            records = {'3624': [{'id': '3624', 'name': 'Klosterneuburg'}],
                       '4063': [{'id': '4063', 'name': 'CANTUS Database'}],
                       '124104': [{'id': '124104', 'display_name': 'Debra Lacoste'}],
                       '4212': [{'id': '4212', 'name': 'Published / Complete'}],
                       '3841': [{'id': '3841', 'name': '14th century'}],
                      }
            return make_future(records[q_id])
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

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_make_extra_fields_unit_1(self, mock_ask_solr):
        "with both a feast_id and source_status_id to look up"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {'feast_desc': 'boiled goose and collard greens', 'source_status_desc': 'Ready'}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!

        def fake_solr(q_type, q_id):
            records = {'123': [{'id': '123', 'description': 'boiled goose and collard greens'}],
                       '456': [{'id': '456', 'description': 'Ready'}],
                      }
            return make_future(records[q_id])
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.handler.make_extra_fields(record, orig_record)

        mock_ask_solr.assert_any_call('feast', '123')
        mock_ask_solr.assert_any_call('source_status', '456')
        # etc.
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_make_extra_fields_unit_2(self, mock_ask_solr):
        "with both a feast_id and source_status_id to look up, but they both return nothing"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!

        def fake_solr(q_type, q_id):
            return make_future({})
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.handler.make_extra_fields(record, orig_record)

        mock_ask_solr.assert_any_call('feast', '123')
        mock_ask_solr.assert_any_call('source_status', '456')
        # etc.
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_make_extra_fields_unit_3(self, mock_ask_solr):
        "with neither a feast_id nor a source_status_id to look up"
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {}
        self.handler.returned_fields = ['id']  # remove everything, so we get nothing back

        def fake_solr(q_type, q_id):
            return make_future({})
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.handler.make_extra_fields(record, orig_record)

        self.assertEqual(0, mock_ask_solr.call_count)
        # etc.
        self.assertEqual(expected, actual)

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_1(self, mock_ask_solr):
        '''
        With many xreffed fields; feast_description to make up; and include "resources"
        '''
        record = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                  'mode': '2S'}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre': 'Responsory Verse',
                               'cantus_id': '600482a', 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'},
                    'resources': {'357679': {'self': '/chants/357679/', 'genre': '/genres/161/',
                                             'feast': '/feasts/2378/'}}}

        def fake_solr(q_type, q_id):
            records = {'357679': [record],
                       '161': [{'name': 'V', 'description': 'Responsory Verse'}],
                       '600482a': [],  # empty until we decide on fill_from_cantusid()
                       '2378': [{'name': 'Jacobi', 'description': 'James the Greater, Aspotle'}],
                      }
            return make_future(records[q_id])
        mock_ask_solr.side_effect = fake_solr

        actual = yield self.http_client.fetch(self.get_url('/chants/357679/'), method='GET')

        self.check_standard_header(actual)
        mock_ask_solr.assert_any_call('chant', '357679')
        mock_ask_solr.assert_any_call('genre', '161')
        mock_ask_solr.assert_any_call('feast', '2378')
        # right now, the "cantusid" won't be looked up unless "feast_id" is missing
        self.assertEqual(expected, escape.json_decode(actual.body))
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'].lower())

    @mock.patch('abbott.__main__.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_2(self, mock_ask_solr):
        "for the X-Cantus-Fields and X-Cantus-Extra-Fields headers; and with multiple returns"
        recordA = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                   'mode': '2S'}
        recordB = {'id': '111222', 'genre_id': '161', 'feast_id': '2378', 'mode': '2S',
                   'sequence': 4}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre': 'Responsory Verse',
                               'cantus_id': '600482a', 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'},
                    '111222': {'id': '111222', 'type': 'chant', 'genre': 'Responsory Verse',
                               'sequence': 4, 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'}}

        def fake_solr(q_type, q_id):
            records = {'*': [recordA, recordB],
                       '161': [{'name': 'V', 'description': 'Responsory Verse'}],
                       '600482a': [],  # empty until we decide on fill_from_cantusid()
                       '2378': [{'name': 'Jacobi', 'description': 'James the Greater, Aspotle'}],
                      }
            return make_future(records[q_id])
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

    @testing.gen_test
    def test_options_integration_1(self):
        "ensure the OPTIONS method works as expected"
        actual = yield self.http_client.fetch(self.get_url('/chants/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual(main.ComplexHandler._ALLOWED_METHODS, actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))

    @testing.gen_test
    def test_get_unit_1(self):
        '''
        For the basic functionality specifically in get():
        - two records
        - four fields
        - X-Cantus-Include-Resources is "true"
        - two fields in only one record
        - two fields must be LOOKUP-ed
        '''
        response = {'1': {'a': 'A', 'b': 'B', 'feast': 'C', 'genre': 'D'},
                    '2': {'a': 'A', 'feast': 'C'},
                    'resources': {'all': 'right'}}
        self.handler.get_handler = mock.Mock(return_value=make_future(response))
        self.handler.write = mock.Mock()
        self.handler.add_header = mock.Mock()
        self.handler.field_counts = {'a': 2, 'b': 1, 'feast_id': 2, 'genre_id': 1}
        exp_include_resources = 'true'
        exp_fields = 'type,a,feast'
        exp_fields_rev = 'type,feast,a'
        exp_extra_fields = 'b,genre'
        exp_extra_fields_rev = 'genre,b'
        resource_id = '1234'

        actual = yield self.handler.get(resource_id)

        self.handler.get_handler.assert_called_once_with(resource_id)
        self.handler.write.assert_called_once_with(response)
        self.assertEqual(3, self.handler.add_header.call_count)
        self.handler.add_header.assert_any_call('X-Cantus-Include-Resources', exp_include_resources)
        # for these next two checks, there are two acceptable orderings for the values; I'm sure
        # there's a better way to do this, but it works for now
        try:
            self.handler.add_header.assert_any_call('X-Cantus-Fields', exp_fields)
        except AssertionError:
            self.handler.add_header.assert_any_call('X-Cantus-Fields', exp_fields_rev)
        try:
            self.handler.add_header.assert_any_call('X-Cantus-Extra-Fields', exp_extra_fields)
        except AssertionError:
            self.handler.add_header.assert_any_call('X-Cantus-Extra-Fields', exp_extra_fields_rev)

    @testing.gen_test
    def test_get_unit_2(self):
        '''
        For the basic functionality specifically in get():
        - same as test_get_unit_1() except...
        - X-Cantus-Include-Resources is "false"

        (Yes, all the checks are still necessary, because self.include_resources may affect
         other things if it's messed up a bit).
        '''
        response = {'1': {'a': 'A', 'b': 'B', 'feast': 'C', 'genre': 'D'},
                    '2': {'a': 'A', 'feast': 'C'}}
        self.handler.get_handler = mock.Mock(return_value=make_future(response))
        self.handler.write = mock.Mock()
        self.handler.add_header = mock.Mock()
        self.handler.field_counts = {'a': 2, 'b': 1, 'feast_id': 2, 'genre_id': 1}
        self.handler.include_resources = False
        exp_include_resources = 'false'
        exp_fields = 'type,a,feast'
        exp_fields_rev = 'type,feast,a'
        exp_extra_fields = 'b,genre'
        exp_extra_fields_rev = 'genre,b'
        resource_id = '1234'

        actual = yield self.handler.get(resource_id)

        self.handler.get_handler.assert_called_once_with(resource_id)
        self.handler.write.assert_called_once_with(response)
        self.assertEqual(3, self.handler.add_header.call_count)
        self.handler.add_header.assert_any_call('X-Cantus-Include-Resources', exp_include_resources)
        # for these next two checks, there are two acceptable orderings for the values; I'm sure
        # there's a better way to do this, but it works for now
        try:
            self.handler.add_header.assert_any_call('X-Cantus-Fields', exp_fields)
        except AssertionError:
            self.handler.add_header.assert_any_call('X-Cantus-Fields', exp_fields_rev)
        try:
            self.handler.add_header.assert_any_call('X-Cantus-Extra-Fields', exp_extra_fields)
        except AssertionError:
            self.handler.add_header.assert_any_call('X-Cantus-Extra-Fields', exp_extra_fields_rev)
