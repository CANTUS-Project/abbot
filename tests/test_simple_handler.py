#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_simple_handler.py
# Purpose:                Tests for the Abbott server's SimpleHandler.
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
Tests for the Abbott server's SimpleHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock
from tornado import escape, httpclient, testing
from abbott import __main__ as main
from abbott import handlers
import shared


class TestInitialize(shared.TestHandler):
    '''
    Tests for the SimpleHandler.initialize().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestInitialize, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    def test_initialize_1(self):
        "initialize() works with no extra fields"
        self.assertEqual('century', self.handler.type_name)
        self.assertEqual('centuries', self.handler.type_name_plural)
        self.assertEqual(4, len(self.handler.returned_fields))
        self.assertIsNone(self.handler.per_page)
        self.assertIsNone(self.handler.page)

    def test_initialize_2(self):
        "initialize() works with extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'TRue'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = handlers.SimpleHandler(self.get_app(), request, type_name='genre',
                                    additional_fields=['mass_or_office'])
        self.assertEqual('genre', actual.type_name)
        self.assertEqual('genres', actual.type_name_plural)
        self.assertEqual(5, len(actual.returned_fields))
        self.assertTrue('mass_or_office' in actual.returned_fields)
        self.assertTrue(actual.include_resources)

    def test_initialize_3(self):
        "initialize() works with extra fields (different values)"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'fALSe',
                                                  'X-Cantus-Per-Page': '9001',
                                                  'X-Cantus-Page': '3'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = handlers.SimpleHandler(self.get_app(), request, type_name='twist')
        self.assertFalse(actual.include_resources)
        self.assertEqual('9001', actual.per_page)
        self.assertEqual('3', actual.page)


class TestFormatRecord(shared.TestHandler):
    '''
    Tests for the SimpleHandler.format_record().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestFormatRecord, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    def test_format_record_1(self):
        "basic test"
        input_record = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}
        input_record['false advertising'] = 'not allowed'  # this key should never appear "for real"
        expected = {key: str(i) for i, key in enumerate(self.handler.returned_fields)}

        actual = self.handler.format_record(input_record)

        self.assertEqual(expected, actual)
        # ensure fields were counted properly
        self.assertEqual(len(self.handler.returned_fields), len(self.handler.field_counts))
        for field in self.handler.returned_fields:
            self.assertEqual(1, self.handler.field_counts[field])


class TestMakeResourceUrl(shared.TestHandler):
    '''
    Tests for the SimpleHandler.make_resource_url().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestMakeResourceUrl, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

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


class TestBasicGetUnit(shared.TestHandler):
    '''
    Unit tests for the SimpleHandler.basic_get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestBasicGetUnit, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_1(self, mock_ask_solr):
        '''
        - with no resource_id and Solr response has three things
        - self.page is None
        - self.sort is None
        '''
        resource_id = None
        mock_solr_response = shared.make_results([{'id': '1'}, {'id': '2'}, {'id': '3'}])
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=None,
                                              rows=None, sort=None)
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_2(self, mock_ask_solr):
        '''
        - when the id ends with '/' and the Solr response is empty (returns 404)
        '''
        resource_id = '123/'
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.send_error = mock.Mock()
        expected_reason = handlers.SimpleHandler._ID_NOT_FOUND.format('century', resource_id[:-1])

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '123')
        self.assertIsNone(actual)
        self.handler.send_error.assert_called_once_with(404, reason=expected_reason)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_3(self, mock_ask_solr):
        '''
        - with resource_id not ending with '/' and Solr response has one thing
        - self.page is defined but self.per_page isn't
        - self.sort is defined
        '''
        resource_id = '888'  # such good luck
        mock_solr_response = shared.make_results([{'id': '888'}])
        expected = {'888': {'id': '888', 'type': 'century'},
                    'resources': {'888': {'self': '/centuries/888/'}}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.page = 4
        self.handler.sort = 'incipit asc'

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '888')
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_4(self, mock_ask_solr):
        '''
        - test_basic_get_unit_1() with self.include_resources set to False
        - self.page and self.per_page are both set
        '''
        resource_id = None
        mock_solr_response = shared.make_results([{'id': '1'}, {'id': '2'}, {'id': '3'}])
        expected = {'1': {'id': '1', 'type': 'century'}, '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.page = 4
        self.handler.per_page = 12

        self.handler.include_resources = False
        actual = yield self.handler.basic_get(resource_id)

        # "start" should be 36, not 48, because the first "page" is numbered 1, which means a
        # "start" of 0, so "page" 2 should have a "start" equal to "per_page" (12 in this test)
        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=36,
                                              rows=12, sort=None)
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_basic_get_unit_5(self, mock_ask_solr):
        '''
        - when the Solr response is empty and self.page is too high (returns 400)
        '''
        resource_id = '123'
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        self.handler.send_error = mock.Mock()
        self.handler.page = 6000

        actual = yield self.handler.basic_get(resource_id)

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '123')
        self.assertIsNone(actual)
        self.handler.send_error.assert_called_once_with(400, reason=handlers.SimpleHandler._TOO_LARGE_PAGE)


class TestGetIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestGetIntegration, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_1(self, mock_ask_solr):
        "test_basic_get_unit_1() but through the whole App infrastructure (thus using get())"
        mock_solr_response = shared.make_results([{'id': '1', 'name': 'one'},
                                                  {'id': '2', 'name': 'two'},
                                                  {'id': '3', 'name': 'three'}])
        expected = {'1': {'id': '1', 'name': 'one', 'type': 'century'},
                    '2': {'id': '2', 'name': 'two', 'type': 'century'},
                    '3': {'id': '3', 'name': 'three', 'type': 'century'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        expected_fields = ['id', 'name', 'type']

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET')

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=None,
                                              rows=None, sort=None)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertCountEqual(expected_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_2(self, mock_ask_solr):
        "returns 400 when X-Cantus-Per-Page is set improperly"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': 'force'})

        self.assertEqual(0, mock_ask_solr.call_count)
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(handlers.SimpleHandler._INVALID_PER_PAGE, actual.reason)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_3(self, mock_ask_solr):
        "returns 400 when X-Cantus-Page is set too high"
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '10'})

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=100,
                                              rows=None, sort=None)
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(handlers.SimpleHandler._TOO_LARGE_PAGE, actual.reason)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_4(self, mock_ask_solr):
        "ensure the X-Cantus-Fields request header works"
        mock_solr_response = shared.make_results([{'id': '1', 'name': 'one'},
                                                  {'id': '2', 'name': 'two'},
                                                  {'id': '3', 'name': 'three'}])
        expected = {'1': {'id': '1', 'type': 'century'},
                    '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'},
                    'resources': {'1': {'self': '/centuries/1/'},
                                  '2': {'self': '/centuries/2/'},
                                  '3': {'self': '/centuries/3/'}}}
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        expected_fields = ['id', 'type']
        request_header = 'id, type'

        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              headers={'X-Cantus-Fields': request_header})

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=None,
                                              rows=None, sort=None)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertCountEqual(expected_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_get_integration_5(self, mock_ask_solr):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Fields': 'id, type,price'})

        self.assertEqual(0, mock_ask_solr.call_count)
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(handlers.SimpleHandler._INVALID_FIELDS, actual.reason)


class TestOptionsIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.options().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    @testing.gen_test
    def test_options_integration_1a(self):
        "ensure the OPTIONS method works as expected ('browse' URL)"
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-Per-Page',
                            'X-Cantus-Page', 'X-Cantus-Sort']
        actual = yield self.http_client.fetch(self.get_url('/genres/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual(handlers.SimpleHandler._ALLOWED_METHODS, actual.headers['Allow'])
        self.assertEqual(0, len(actual.body))
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_options_integration_2a(self, mock_ask_solr):
        "OPTIONS request for non-existent resource gives 404"
        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        actual = yield self.http_client.fetch(self.get_url('/genres/nogenre/'),
                                              method='OPTIONS',
                                              raise_error=False)
        self.check_standard_header(actual)
        self.assertEqual(404, actual.code)
        mock_ask_solr.assert_called_once_with('genre', 'nogenre')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_options_integration_2b(self, mock_ask_solr):
        "OPTIONS request for existing resource returns properly ('view' URL)"
        expected_headers = ['X-Cantus-Include-Resources', 'X-Cantus-Fields']
        mock_solr_response = shared.make_results(['Versicle'])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        actual = yield self.http_client.fetch(self.get_url('/genres/162/'), method='OPTIONS')
        self.check_standard_header(actual)
        self.assertEqual(0, len(actual.body))
        mock_ask_solr.assert_called_once_with('genre', '162')
        for each_header in expected_headers:
            self.assertEqual('allow', actual.headers[each_header].lower())


class TestHeadIntegration(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.head().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestHeadIntegration, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbott.util.ask_solr_by_id')
    @testing.gen_test
    def test_head_integration_1a(self, mock_ask_solr):
        "test_get_integration_1() but with the HEAD method"
        mock_solr_response = shared.make_results([{'id': '1'}, {'id': '2'}, {'id': '3'}])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='HEAD')

        mock_ask_solr.assert_called_once_with(self.handler.type_name, '*', start=None,
                                              rows=None, sort=None)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertEqual(0, len(actual.body))


class TestVerifyRequestHeaders(shared.TestHandler):
    '''
    Unit tests for SimpleHandler.verify_request_headers().

    Note that I could have combined these things into fewer tests, but I'm trying a new strategy
    to minimize the things tested per test, rather than trying to minimize the number of tests.
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestVerifyRequestHeaders, self).setUp()
        self.request = httpclient.HTTPRequest(url='/zool/', method='GET')
        self.request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = handlers.SimpleHandler(self.get_app(), self.request, type_name='century')

    def setup_with_complex(self):
        "replace self.handler with a ComplexHandler instance"
        self.handler = handlers.ComplexHandler(self.get_app(), self.request, type_name='chant')

    def test_vrh_template(self, **kwargs):
        '''
        PLEASE READ THIS WHOLE DOCSTRING BEFORE YOU MODIFY ONE OF THESE TESTS.

        This is a template test. Without kwargs, it runs verify_request_headers() with "default"
        settings, as far as that's posssible. Here are the default values for the kwargs:

        - is_browse_request = True
        - no_xref = False
            - exp_no_xref = False
        - fields = None
            - exp_fields = ['id', 'type', 'name', 'description'] -- NOTE this is compared against self.required_fields
        - per_page = None
            - exp_per_page = None
        - page = None
            - exp_page = None
        - sort = None
            - exp_sort = None

        **However** if is_browse_request is set to False in the kwargs, "canary" values are used for
        the following header variables, which should be ignored by verify_request_headers():

        - per_page = 'garbage'
            - exp_per_page = 'garbage'
        - page = 'test'
            - exp_page = 'test'
        - sort = 'data'
            - exp_sort = 'data'

        ------------------------

        The following kwargs also exist:

        :kwarg bool use_complex_handler: Whether to call :meth:`setup_with_complex` before the test.
            Use this for tests about self.no_xref.
        :kwarg bool mock_send_error: Whether to install a dummy mock onto send_error(). Default is
            True. If you send a Mock object, it will be attached appropriately, so you can run
            assertions on it once this test method returns.
        :kwarg int send_error_count: The number of calls to SimpleHandler.send_error(). Default is
            no calls. This is checked if :meth:`send_error` is a :class:`Mock` object, regardless of
            the setting of "mock_send_error," so that it works even if you mock that method yourself.
            NOTE that if "expected" is False, this default changes to 1.
        :kwarg bool expected: The expected return value of the method. Default is True. NOTE that
            if "expected" is False, checks related to the header fields are skipped, and you should
            check :meth:`send_error` and adjust "send_error_count" as required.
        '''

        def set_default(key, val):
            "Check in kwargs if 'key' is defined; if not, set it to 'val'."
            if key not in kwargs:
                kwargs[key] = val

        # set default kwargs
        set_default('use_complex_handler', False)
        set_default('mock_send_error', True)
        set_default('is_browse_request', True)
        set_default('expected', True)
        set_default('no_xref', False)
        set_default('exp_no_xref', False)
        set_default('fields', None)
        set_default('exp_fields', ['id', 'type', 'name', 'description'])
        if kwargs['is_browse_request']:
            set_default('per_page', None)
            set_default('exp_per_page', None)
            set_default('page', None)
            set_default('exp_page', None)
            set_default('sort', None)
            set_default('exp_sort', None)
        else:
            set_default('per_page', 'garbage')
            set_default('exp_per_page', 'garbage')
            set_default('page', 'test')
            set_default('exp_page', 'test')
            set_default('sort', 'data')
            set_default('exp_sort', 'data')
        if kwargs['expected'] is False:
            set_default('send_error_count', 1)
        else:
            set_default('send_error_count', 0)

        if kwargs['use_complex_handler']:
            self.setup_with_complex()
        if kwargs['mock_send_error'] is True:
            mock_send_error = mock.Mock()
            self.handler.send_error = mock_send_error
        elif kwargs['mock_send_error']:
            self.handler.send_error = kwargs['mock_send_error']
        self.handler.no_xref = kwargs['no_xref']
        self.handler.fields = kwargs['fields']
        self.handler.per_page = kwargs['per_page']
        self.handler.page = kwargs['page']
        self.handler.sort = kwargs['sort']

        actual = self.handler.verify_request_headers(kwargs['is_browse_request'])

        self.assertEqual(kwargs['expected'], actual)
        if kwargs['expected'] is True:
            self.assertEqual(kwargs['exp_no_xref'], self.handler.no_xref)
            self.assertEqual(kwargs['exp_fields'], self.handler.returned_fields)
            self.assertEqual(kwargs['exp_per_page'], self.handler.per_page)
            self.assertEqual(kwargs['exp_page'], self.handler.page)
            self.assertEqual(kwargs['exp_sort'], self.handler.sort)
        if isinstance(self.handler.send_error, mock.Mock):
            self.assertEqual(kwargs['send_error_count'], self.handler.send_error.call_count)


    def test_not_browse_request_1(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.no_xref is False & self.fields is None (their defaults)
        - other fields have invalid canary values

        Postconditions:
        - they're both still the same
        - all the other fields still have canary values
        - method returns True
        '''
        self.test_vrh_template(use_complex_handler=True, is_browse_request=False)

    def test_not_browse_request_2(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.no_xref is 'true'
        - other fields have invalid canary values

        Postconditions:
        - self.no_xref comes out as True
        - all the other fields still have canary values
        - method returns True
        '''
        self.test_vrh_template(use_complex_handler=True,
                               is_browse_request=False,
                               no_xref='  trUE         ',
                               exp_no_xref=True)

    def test_not_browse_request_3(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.no_xref is 'false'
        - other fields have invalid canary values

        Postconditions:
        - self.no_xref comes out as False
        - all the other fields still have canary values
        - method returns True
        '''
        self.test_vrh_template(use_complex_handler=True,
                               is_browse_request=False,
                               no_xref='   falSe')

    def test_not_browse_request_4(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.no_xref is 'soup'
        - other fields have invalid canary values

        Postconditions:
        - send_error() called
        - method returns False
        '''
        mock_send_error = mock.Mock()

        self.test_vrh_template(use_complex_handler=True,
                               is_browse_request=False,
                               no_xref='soup',
                               mock_send_error=mock_send_error,
                               expected=False)

        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._INVALID_NO_XREF)

    def test_not_browse_request_5(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.no_xref is invalid BUT it's a SimpleHandler
        - other fields have invalid canary values

        Postconditions:
        - they're both still None
        - all the other fields still have canary values
        - method returns True
        '''
        self.test_vrh_template(use_complex_handler=False,
                               is_browse_request=False,
                               no_xref='soup',
                               exp_no_xref='soup')

    @mock.patch('abbott.util.parse_fields_header')
    def test_not_browse_request_6(self, mock_pfh):
        '''
        Preconditions:
        - self.fields is some value
        - parse_fields_header mock returns fine

        Postconditions:
        - they're both still None
        - all the other fields still have canary values
        - method returns True
        '''
        fields = 'something'
        parse_fields_header_return = 'whatever'
        mock_pfh.return_value = parse_fields_header_return

        self.test_vrh_template(is_browse_request=False,
                               fields=fields,
                               exp_fields=parse_fields_header_return)

        mock_pfh.assert_called_once_with('something', ['id', 'type', 'name', 'description'])

    @mock.patch('abbott.util.parse_fields_header')
    def test_not_browse_request_7(self, mock_pfh):
        '''
        Preconditions:
        - self.fields is some value
        - parse_fields_header mock raises ValueError

        Postconditions:
        - send_error() is called
        - method returns False
        '''
        fields = 'something'
        mock_pfh.side_effect = ValueError
        mock_send_error = mock.Mock()

        self.test_vrh_template(is_browse_request=False,
                               fields=fields,
                               expected=False,
                               mock_send_error=mock_send_error)

        mock_pfh.assert_called_once_with('something', ['id', 'type', 'name', 'description'])
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._INVALID_FIELDS)

    @mock.patch('abbott.util.parse_fields_header')
    def test_not_browse_request_8(self, mock_pfh):
        '''
        Preconditions:
        - self.fields is some value
        - self.no_xref is 'soup' (and this is a ComplexHandler
        - parse_fields_header mock raises ValueError

        Postconditions:
        - send_error() is called with "body" argument
        - method returns False
        '''
        fields = 'something'
        mock_pfh.side_effect = ValueError
        mock_send_error = mock.Mock()

        self.test_vrh_template(use_complex_handler=True,
                               is_browse_request=False,
                               no_xref='soup',
                               fields=fields,
                               expected=False,
                               mock_send_error=mock_send_error)

        mock_pfh.assert_called_once_with('something', ['id', 'type', 'name', 'description'])
        mock_send_error.assert_called_with(400,
                                           reason=handlers.SimpleHandler._MANY_BAD_HEADERS,
                                           body=[handlers.SimpleHandler._INVALID_NO_XREF,
                                                 handlers.SimpleHandler._INVALID_FIELDS])

    def test_browse_request_1(self):
        '''
        Preconditions:
        - per_page is an int (as a string when inputted) in the valid range

        Postconditions:
        - per_page becomes an actual int
        '''
        self.test_vrh_template(per_page='14', exp_per_page=14)

    def test_browse_request_2(self):
        '''
        Preconditions:
        - per_page isn't an int

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, per_page='five')
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._INVALID_PER_PAGE)

    def test_browse_request_3(self):
        '''
        Preconditions:
        - per_page is an int, but less than zero

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, per_page='-3')
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._TOO_SMALL_PER_PAGE)

    def test_browse_request_4(self):
        '''
        Preconditions:
        - per_page is an int, but greater than _MAX_PER_PAGE

        Postconditions:
        - send_error() called *with 507*
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, per_page='40000000')
        mock_send_error.assert_called_with(507,
                                           reason=handlers.SimpleHandler._TOO_BIG_PER_PAGE,
                                           per_page=handlers.SimpleHandler._MAX_PER_PAGE)

    def test_browse_request_5(self):
        '''
        Preconditions:
        - per_page is 0

        Postconditions:
        - per_page becomes _MAX_PER_PAGE
        '''
        self.test_vrh_template(per_page='0', exp_per_page=handlers.SimpleHandler._MAX_PER_PAGE)

    def test_browse_request_6(self):
        '''
        Preconditions:
        - page is not an int

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, page='two')
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._INVALID_PAGE)

    def test_browse_request_7(self):
        '''
        Preconditions:
        - page is an int (as a string when inputted) greater than 1

        Postconditions:
        - it is returned fine
        '''
        self.test_vrh_template(page='2', exp_page=2)

    def test_browse_request_8(self):
        '''
        Preconditions:
        - page is an int, but 1

        Postconditions:
        - it is returned fine
        '''
        self.test_vrh_template(page='1', exp_page=1)

    def test_browse_request_9(self):
        '''
        Preconditions:
        - page is an int, less than 1

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, page='0')
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._TOO_SMALL_PAGE)

    def test_browse_request_10(self):
        '''
        Preconditions:
        - sort is valid

        Postconditions:
        - returns fine
        '''
        self.test_vrh_template(sort='name,asc', exp_sort='name asc')

    def test_browse_request_11(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises ValueError with _MISSING_DIRECTION_SPEC

        Postconditions:
        - send_error() called with _MISSING_DIRECTION_SPEC
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='name')
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._MISSING_DIRECTION_SPEC)

    def test_browse_request_12(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises ValueError because of an invalid character

        Postconditions:
        - send_error() called with _DISALLOWED_CHARACTER_IN_SORT
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='n!me,asc')
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._DISALLOWED_CHARACTER_IN_SORT)

    def test_browse_request_13(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises KeyError

        Postconditions:
        - send_error() called with _UNKNOWN_FIELD
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='nime,asc')
        mock_send_error.assert_called_with(400, reason=handlers.SimpleHandler._UNKNOWN_FIELD)

    def test_browse_request_14(self):
        '''
        Preconditions:
        - per_page is '-4'
        - page is 'yes'
        - no_xref is 'soup'
        - it's a ComplexHandler

        Postconditions:
        - send_error() called with _TOO_SMALL_PER_PAGE; _INVALID_PAGE; _INVALID_NO_XREF
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, use_complex_handler=True,
                               per_page='-4', page='yes', no_xref='soup')
        mock_send_error.assert_called_with(400,
                                           reason=handlers.SimpleHandler._MANY_BAD_HEADERS,
                                           body=[handlers.SimpleHandler._TOO_SMALL_PER_PAGE,
                                                 handlers.SimpleHandler._INVALID_PAGE,
                                                 handlers.SimpleHandler._INVALID_NO_XREF])
