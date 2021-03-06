#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_simple_handler.py
# Purpose:                Tests for the Abbot server's SimpleHandler.
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
Tests for the Abbot server's SimpleHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

from unittest import mock
from tornado import httpclient

import abbot
from abbot import __main__ as main
from abbot.complex_handler import ComplexHandler
from abbot import simple_handler
from abbot.simple_handler import SimpleHandler
import shared


class TestInitialize(shared.TestHandler):
    '''
    Tests for the SimpleHandler.initialize().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def test_initialize_1(self):
        "initialize() works with no extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='century')
        self.assertEqual('century', actual.type_name)
        self.assertEqual('centuries', actual.type_name_plural)
        self.assertEqual(4, len(actual.returned_fields))
        self.assertIsNone(actual.hparams['per_page'])
        self.assertIsNone(actual.hparams['page'])

    def test_initialize_2(self):
        "initialize() works with extra fields"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'TRue'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='genre',
                               additional_fields=['mass_or_office'])
        self.assertEqual('genre', actual.type_name)
        self.assertEqual('genres', actual.type_name_plural)
        self.assertEqual(5, len(actual.returned_fields))
        self.assertTrue('mass_or_office' in actual.returned_fields)
        self.assertTrue(actual.hparams['include_resources'])

    def test_initialize_3(self):
        "initialize() works with extra fields (different values)"
        request = httpclient.HTTPRequest(url='/zool/', method='GET',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-Fields': 'code black'})
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='feast')
        self.assertEqual('code red', actual.hparams['include_resources'])
        self.assertEqual('code blue', actual.hparams['per_page'])
        self.assertEqual('code green', actual.hparams['page'])
        self.assertEqual('code white', actual.hparams['sort'])
        self.assertEqual('code black', actual.hparams['fields'])

    def test_initialize_4(self):
        "initialize() works with SEARCH request (no values set in request body)"
        request = httpclient.HTTPRequest(url='/zool/', method='SEARCH',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-Fields': 'code black'},
                                         body='{}')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='feast')
        self.assertEqual('code red', actual.hparams['include_resources'])
        self.assertEqual('code blue', actual.hparams['per_page'])
        self.assertEqual('code green', actual.hparams['page'])
        self.assertEqual('code white', actual.hparams['sort'])
        self.assertEqual('code black', actual.hparams['fields'])

    def test_initialize_5(self):
        "initialize() works with SEARCH request (all values set in request body)"
        request = httpclient.HTTPRequest(url='/zool/', method='SEARCH',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-Fields': 'code black'},
                                         body='{"include_resources": "red code",'
                                               '"per_page": "blue code",'
                                               '"page": "green code",'
                                               '"sort": "white code",'
                                               '"fields": "black code",'
                                               '"query": "whatever"}')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='feast')
        self.assertEqual('red code', actual.hparams['include_resources'])
        self.assertEqual('blue code', actual.hparams['per_page'])
        self.assertEqual('green code', actual.hparams['page'])
        self.assertEqual('white code', actual.hparams['sort'])
        self.assertEqual('black code', actual.hparams['fields'])
        self.assertEqual('whatever', actual.hparams['search_query'])

    @mock.patch('abbot.simple_handler.SimpleHandler.send_error')
    def test_initialize_6(self, mock_send_error):
        "initialize() works with SEARCH request (JSON is faulty)"
        request = httpclient.HTTPRequest(url='/zool/', method='SEARCH',
                                         headers={'X-Cantus-Include-Resources': 'code red',
                                                  'X-Cantus-Per-Page': 'code blue',
                                                  'X-Cantus-Page': 'code green',
                                                  'X-Cantus-Sort': 'code white',
                                                  'X-Cantus-Fields': 'code black'},
                                         body='{include_resources: "red code"}')
        request.connection = mock.Mock()  # required for Tornado magic things
        actual = SimpleHandler(self.get_app(), request, type_name='feast')
        self.assertIsNone(actual.hparams['search_query'])
        mock_send_error.assert_called_once_with(400, reason=simple_handler._MISSING_SEARCH_BODY)

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
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')

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

    def test_drupal_urls_enabled(self):
        '''
        format_record() properly handles "drupal_path" when the Drupal URL is set.
        '''
        self._simple_options.drupal_url = 'http://can.tus/'
        input_record = {'id': '123', 'drupal_path': '/anon/y/mous/34432/blob.xhtml'}

        actual = self.handler.format_record(input_record)

        assert {'id': '123', 'drupal_path': 'http://can.tus/anon/y/mous/34432/blob.xhtml'} == actual

    def test_drupal_urls_disabled(self):
        '''
        format_record() omits "drupal_path" when the Drupal URL is not set.
        '''
        self._simple_options.drupal_url = None
        input_record = {'id': '123', 'drupal_path': '/anon/y/mous/34432/blob.xhtml'}

        actual = self.handler.format_record(input_record)

        assert {'id': '123'} == actual


class TestMakeResourceUrl(shared.TestHandler):
    '''
    Tests for the SimpleHandler.make_resource_url() and SimpleHandler.make_drupal_url().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestMakeResourceUrl, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')

    def test_make_resource_url_1(self):
        "with no resource_type specified"
        expected = 'https://cantus.org/centuries/420/'
        actual = self.handler.make_resource_url('420')
        self.assertEqual(expected, actual)

    def test_make_resource_url_2(self):
        "with singuler resource_type"
        expected = 'https://cantus.org/chants/69/'
        actual = self.handler.make_resource_url('69', 'chant')
        self.assertEqual(expected, actual)

    def test_make_resource_url_3(self):
        "with plural resource_type"
        expected = 'https://cantus.org/sources/3.14159/'
        actual = self.handler.make_resource_url('3.14159', 'sources')
        self.assertEqual(expected, actual)


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
        self.handler = SimpleHandler(self.get_app(), self.request, type_name='century')

    def setup_with_complex(self):
        "replace self.handler with a ComplexHandler instance"
        self.handler = ComplexHandler(self.get_app(), self.request, type_name='chant')

    def test_vrh_template(self, **kwargs):
        '''
        PLEASE READ THIS WHOLE DOCSTRING BEFORE YOU MODIFY ONE OF THESE TESTS.

        This is a template test. Without kwargs, it runs verify_request_headers() with "default"
        settings, as far as that's posssible. Here are the default values for the kwargs:

        - is_browse_request = True
        - include_resources = True
            - exp_include_resources = True
        - fields = None
            - exp_fields = ['id', 'type', 'name', 'description']
                - NOTE: exp_fields is compared against self.required_fields
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

        Those "canary" values must be reset to ``None`` after verify_request_headers() runs. If the
        values are allowed to stay, other parts of Abbot may interpret them as legitimate values,
        even though they are supposed to be ignored for "view" requests.

        ------------------------

        The following kwargs also exist:

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
        set_default('mock_send_error', True)
        set_default('is_browse_request', True)
        set_default('expected', True)
        set_default('include_resources', True)
        set_default('exp_include_resources', True)
        set_default('fields', None)
        set_default('exp_fields', ['id', 'type', 'name', 'description'])
        if kwargs['is_browse_request']:
            set_default('per_page', None)
            set_default('exp_per_page', 10)
            set_default('page', None)
            set_default('exp_page', 1)
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

        if kwargs['mock_send_error'] is True:
            mock_send_error = mock.Mock()
            self.handler.send_error = mock_send_error
        elif kwargs['mock_send_error']:
            self.handler.send_error = kwargs['mock_send_error']
        self.handler.hparams['fields'] = kwargs['fields']
        self.handler.hparams['per_page'] = kwargs['per_page']
        self.handler.hparams['page'] = kwargs['page']
        self.handler.hparams['sort'] = kwargs['sort']
        self.handler.hparams['include_resources'] = kwargs['include_resources']

        actual = self.handler.verify_request_headers(kwargs['is_browse_request'])

        self.assertEqual(kwargs['expected'], actual)
        if kwargs['expected'] is True:
            self.assertEqual(kwargs['exp_fields'], self.handler.returned_fields)
            if kwargs['is_browse_request']:
                self.assertEqual(kwargs['exp_per_page'], self.handler.hparams['per_page'])
                self.assertEqual(kwargs['exp_page'], self.handler.hparams['page'])
                self.assertEqual(kwargs['exp_sort'], self.handler.hparams['sort'])
            else:
                assert self.handler.hparams['per_page'] is None
                assert self.handler.hparams['page'] is None
                assert self.handler.hparams['sort'] is None
            self.assertEqual(kwargs['exp_include_resources'], self.handler.hparams['include_resources'])
        if isinstance(self.handler.send_error, mock.Mock):
            self.assertEqual(kwargs['send_error_count'], self.handler.send_error.call_count)


    def test_not_browse_request_1(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['fields'] is None (its default)
        - self.hparams['include_resources'] is True (its default)
        - other fields have invalid canary values

        Postconditions:
        - they're both still the same
        - all the other fields still have canary values
        - method returns True
        '''
        self.test_vrh_template(is_browse_request=False)

    @mock.patch('abbot.util.parse_fields_header')
    def test_not_browse_request_2(self, mock_pfh):
        '''
        Preconditions:
        - self.hparams['fields'] is some value
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

    @mock.patch('abbot.util.parse_fields_header')
    def test_not_browse_request_3(self, mock_pfh):
        '''
        Preconditions:
        - self.hparams['fields'] is some value
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
        mock_send_error.assert_called_with(400, reason=simple_handler._INVALID_FIELDS)

    def test_not_browse_request_4(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['include_resources'] is '  faLSe  '
        - other fields have invalid canary values

        Postconditions:
        - self.hparams['include_resources'] becomes False
        - method returns True
        '''
        self.test_vrh_template(is_browse_request=False,
                               include_resources='  faLSe  ',
                               exp_include_resources=False)

    def test_not_browse_request_5(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['include_resources'] is '  TRue  '
        - other fields have invalid canary values

        Postconditions:
        - self.hparams['include_resources'] becomes True
        - method returns True
        '''
        self.test_vrh_template(is_browse_request=False,
                               include_resources='  TRue  ',
                               exp_include_resources=True)

    def test_not_browse_request_6(self):
        '''
        Preconditions:
        - is_browse_request = False
        - self.hparams['include_resources'] is 'wristwatch'
        - other fields have invalid canary values

        Postconditions:
        - method returns False
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(is_browse_request=False,
                               include_resources='wristwatch',
                               expected=False,
                               mock_send_error=mock_send_error)
        mock_send_error.assert_called_with(400, reason=simple_handler._BAD_INCLUDE_RESOURCES)

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
        mock_send_error.assert_called_with(400, reason=simple_handler._INVALID_PER_PAGE)

    def test_browse_request_3(self):
        '''
        Preconditions:
        - per_page is an int, but less than zero

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, per_page='-3')
        mock_send_error.assert_called_with(400, reason=simple_handler._TOO_SMALL_PER_PAGE)

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
                                           reason=simple_handler._TOO_BIG_PER_PAGE,
                                           per_page=SimpleHandler._MAX_PER_PAGE)

    def test_browse_request_5(self):
        '''
        Preconditions:
        - per_page is 0

        Postconditions:
        - per_page becomes _MAX_PER_PAGE
        '''
        self.test_vrh_template(per_page='0', exp_per_page=SimpleHandler._MAX_PER_PAGE)

    def test_browse_request_6(self):
        '''
        Preconditions:
        - page is not an int

        Postconditions:
        - send_error() called
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, page='two')
        mock_send_error.assert_called_with(400, reason=simple_handler._INVALID_PAGE)

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
        mock_send_error.assert_called_with(400, reason=simple_handler._TOO_SMALL_PAGE)

    def test_browse_request_10(self):
        '''
        Preconditions:
        - sort is valid

        Postconditions:
        - returns fine
        '''
        self.test_vrh_template(sort='name;asc', exp_sort='name asc')

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
        mock_send_error.assert_called_with(400, reason=simple_handler._MISSING_DIRECTION_SPEC)

    def test_browse_request_12(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises ValueError because of an invalid character

        Postconditions:
        - send_error() called with _DISALLOWED_CHARACTER_IN_SORT
        '''
        mock_send_error = mock.Mock()
        exp_reason = simple_handler._DISALLOWED_CHARACTER_IN_SORT
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='n!me,asc')
        mock_send_error.assert_called_with(400, reason=exp_reason)

    def test_browse_request_13(self):
        '''
        Preconditions:
        - sort is something
        - prepare_formatted_sort() raises KeyError

        Postconditions:
        - send_error() called with _UNKNOWN_FIELD
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, sort='nime;asc')
        mock_send_error.assert_called_with(400, reason=simple_handler._UNKNOWN_FIELD)

    def test_browse_request_14(self):
        '''
        Preconditions:
        - per_page is '-4'
        - page is 'yes'
        - it's a ComplexHandler

        Postconditions:
        - send_error() called with _TOO_SMALL_PER_PAGE; _INVALID_PAGE
        '''
        mock_send_error = mock.Mock()
        self.test_vrh_template(mock_send_error=mock_send_error, expected=False, use_complex_handler=True,
                               per_page='-4', page='yes')
        mock_send_error.assert_called_with(400,
                                           reason=simple_handler._MANY_BAD_HEADERS,
                                           body=[simple_handler._TOO_SMALL_PER_PAGE,
                                                 simple_handler._INVALID_PAGE])


class TestMakeResponseHeaders(shared.TestHandler):
    '''
    Unit tests for SimpleHandler.make_response_headers().

    Note that I could have combined these things into fewer tests, but I'm trying a new strategy
    to minimize the things tested per test, rather than trying to minimize the number of tests.

    Like the tests for :meth:`verify_request_headers`, these tests use a template. Here, I've only
    made additional test methods for the non-default conditions
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestMakeResponseHeaders, self).setUp()
        self.request = httpclient.HTTPRequest(url='/zool/', method='GET')
        self.request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), self.request, type_name='century')

    def test_mrh_template(self, **kwargs):
        '''
        This is a test template for make_response_headers(). By default, the template makes several
        assertions by itself, which are described below.

        You can change a default precondition or the by using the kwargs listed here:
        is_browse_request, num_records, field_counts, include_resources, total_results,
        per_page, page, sort.

        You can change the expected hader value by using the kwargs listed here:
        h_fields, h_extra_fields, h_include_resources, h_total_results, h_per_page,
        h_page, h_sort.

        NOTE that if you set one of the expected header values to ``None``, it is turned into an
        assertion that :meth:`add_header` was not called with that header.

        --------

        These are the "default" pre- and post-conditions.

        Preconditions:
        - is_browse_request is False
        - num_records is 0
        - self.field_counts is {}
        - self.hparams['include_resources'] is True

        Postconditions:
        - X-Cantus-Fields isn't called
        - X-Cantus-Extra-Fields isn't called called
        - X-Cantus-Include_Resources called with 'true'

        --------

        If the "is_browse_request" kwarg is True (not the default), these conditions also apply.

        Additional Preconditions if "is_browse_request" is True:
        - self.total_results is 400
        - self.handler.hparams['per_page'] is None
        - self.hparams['page'] is None
        - self.hparams['sort'] is None

        Additional Postconditions if "is_browse_request" is True:
        - X-Cantus-Total-Results called with 400
        - X-Cantus-Per-Page called with 10
        - X-Cantus-Page called with 1
        - X-Cantus-Sort isn't called
        '''

        def set_default(key, val):
            "Check in kwargs if 'key' is defined; if not, set it to 'val'."
            if key not in kwargs:
                kwargs[key] = val

        # set default values for the kwargs
        set_default('is_browse_request', False)
        set_default('num_records', 0)
        set_default('field_counts', {})
        set_default('include_resources', True)
        set_default('h_fields', None)
        set_default('h_extra_fields', None)
        set_default('h_include_resources', 'true')
        if kwargs['is_browse_request']:
            set_default('total_results', 400)
            set_default('per_page', None)
            set_default('page', None)
            set_default('sort', None)
            set_default('h_total_results', 400)
            set_default('h_per_page', 10)
            set_default('h_page', 1)
            set_default('h_sort', None)

        # prepare the pre-conditions
        self.handler.field_counts = kwargs['field_counts']
        self.handler.hparams['include_resources'] = kwargs['include_resources']
        if kwargs['is_browse_request']:
            self.handler.total_results = kwargs['total_results']
            self.handler.hparams['per_page'] = kwargs['per_page']
            self.handler.hparams['page'] = kwargs['page']
            self.handler.hparams['sort'] = kwargs['sort']

        # run the test
        mock_add_header = mock.Mock()
        self.handler.add_header = mock_add_header
        self.handler.make_response_headers(kwargs['is_browse_request'], kwargs['num_records'])

        # check the headers (that are always present)
        header_correspondences = {'h_fields': 'X-Cantus-Fields',
                                  'h_extra_fields': 'X-Cantus-Extra-Fields',
                                  'h_include_resources': 'X-Cantus-Include-Resources'}
        for key, header in header_correspondences.items():
            if kwargs[key] is None:
                assert mock.call(header, mock.ANY) not in mock_add_header.call_args_list
            elif 'h_fields' == key or 'h_extra_fields' == key:
                # we accept any order for these header values, so it's a little complicated to test
                mock_add_header.assert_any_call(header, mock.ANY)
                for each_call in mock_add_header.call_args_list:
                    if header == each_call[0][0]:
                        self.assertCountEqual(kwargs[key].split(','), each_call[0][1].split(','))
                        break
            else:
                mock_add_header.assert_any_call(header, kwargs[key])

        # check the headers (only if is_browse_request)
        if not kwargs['is_browse_request']:
            return
        header_correspondences = {'h_total_results': 'X-Cantus-Total-Results',
                                  'h_per_page': 'X-Cantus-Per-Page',
                                  'h_page': 'X-Cantus-Page',
                                  'h_sort': 'X-Cantus-Sort'}
        for key, header in header_correspondences.items():
            if kwargs[key] is None:
                assert mock.call(header, mock.ANY) not in mock_add_header.call_args_list
            else:
                mock_add_header.assert_any_call(header, kwargs[key])

    def test_basic_browse_request(self):
        '''
        Calls test_mrh_template() with "is_browse_request" set to True.
        '''
        self.test_mrh_template(is_browse_request=True)

    def test_fields_1(self):
        '''
        Preconditions:
        - num_records is 5
        - self.field_counts has these counts
            - 'name': 5
            - 'id': 5
            - 'feast_code': 3
            - 'type': 3

        Postconditions:
        - X-Cantus-Fields called with something like 'id,name,type'
        - X-Cantus-Extra-Fields called with 'feast_code'
        '''
        self.test_mrh_template(num_records=5,
                               field_counts={'name': 5, 'id': 5, 'feast_code': 3, 'type': 3},
                               h_fields='id,name',
                               h_extra_fields='feast_code,type')

    def test_fields_2(self):
        '''
        Preconditions:
        - num_records is 5
        - self.field_counts has these counts
            - 'name': 5
            - 'id': 5
            - 'feast_code': 5
            - 'type': 5

        Postconditions:
        - X-Cantus-Fields called with something like 'id,name,source,type'
        '''
        self.test_mrh_template(num_records=5,
                               field_counts={'name': 5, 'id': 5, 'feast_code': 5, 'type': 5},
                               h_fields='id,name,type,feast_code')

    def test_resources(self):
        '''
        Preconditions:
        - self.hparams['include_resources'] is False

        Postconditions:
        - self.add_header('X-Cantus-Include-Resources', 'false')
        '''
        self.test_mrh_template(include_resources=False,
                               h_include_resources='false')

    def test_total_results(self):
        '''
        Preconditions:
        - is_browse_request is True
        - self.total_results is 50

        Postconditions:
        - X-Cantus-Total-Results with 50
        '''
        self.test_mrh_template(is_browse_request=True, total_results=50, h_total_results=50)

    def test_per_page(self):
        '''
        Preconditions:
        - is_browse_request is True
        - self.handler.hparams['per_page'] is 14

        Postconditions:
        - X-Cantus-Per-Page with 14
        '''
        self.test_mrh_template(is_browse_request=True, per_page=14, h_per_page=14)

    def test_page(self):
        '''
        Preconditions:
        - is_browse_request is True
        - self.hparams['page'] is 8

        Postconditions:
        - X-Cantus-Page with 8
        '''
        self.test_mrh_template(is_browse_request=True, page=8, h_page=8)

    @mock.patch('abbot.util.postpare_formatted_sort')
    def test_sort(self, mock_pfs):
        '''
        Preconditions:
        - is_browse_request is True
        - self.hparams['sort'] is 'testing sort'

        Postconditions:
        - postpare_formatted_sort() called with 'testing sort' (mock returns 'sorted')
        - X-Cantus-Sort with 'sorted'
        '''
        mock_pfs.return_value = 'sorted'
        self.test_mrh_template(is_browse_request=True, sort='testing sort', h_sort='sorted')
        mock_pfs.assert_called_once_with('testing sort')


class TestSendError(shared.TestHandler):
    '''
    Tests for SimpleHandler.send_error().
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSendError, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')

    @mock.patch('abbot.simple_handler.SimpleHandler.clear')
    @mock.patch('abbot.simple_handler.SimpleHandler.add_header')
    @mock.patch('abbot.simple_handler.SimpleHandler.set_status')
    @mock.patch('abbot.simple_handler.SimpleHandler.write')
    def test_send_error_1(self, mock_write, mock_set_status, mock_add_header, mock_clear):
        '''
        per_page, reason, and response kwargs are all provided.

        Ensure:
        - clear() is called
        - add_header() called with appropriate args
        - set_status() called with appropriate args
        - write() called with appropriate args
        '''
        code = 418
        reason = 'This is a test.'
        per_page = 42
        response = 'Please avoid panicking about this test error.'

        self.handler.send_error(code, reason=reason, per_page=per_page, response=response)

        mock_clear.assert_called_once_with()
        mock_add_header.assert_called_once_with('X-Cantus-Per-Page', per_page)
        mock_set_status.assert_called_once_with(code, reason)
        mock_write.assert_called_once_with(response)

    @mock.patch('abbot.simple_handler.SimpleHandler.clear')
    @mock.patch('abbot.simple_handler.SimpleHandler.add_header')
    @mock.patch('abbot.simple_handler.SimpleHandler.set_status')
    @mock.patch('abbot.simple_handler.SimpleHandler.write')
    def test_send_error_2(self, mock_write, mock_set_status, mock_add_header, mock_clear):
        '''
        per_page, reason, and response kwargs are all omitted.

        Ensure:
        - clear() is called
        - add_header() not called
        - set_status() called with appropriate args            code)
        - write() called with appropriate args                 'code: (no reason given)')
        '''
        code = 418

        self.handler.send_error(code)

        mock_clear.assert_called_once_with()
        self.assertEqual(0, mock_add_header.call_count)
        mock_set_status.assert_called_once_with(code)
        mock_write.assert_called_once_with('{}: (no reason given)'.format(code))

    @mock.patch('abbot.simple_handler.SimpleHandler.add_header')
    def test_send_error_3(self, mock_add_header):
        '''
        With "allow" in the kwargs.

        Ensure:
        - add_header() is called to set the "Allow" header
        '''
        code = 420
        reason = 'blaze it'
        allow = 'GET, PUT'

        self.handler.send_error(code, reason=reason, allow=allow)

        mock_add_header.assert_called_with('Allow', allow)


class TestCorsMethods(shared.TestHandler):
    '''
    Tests for SimpleHandler._cors_preflight() and _cors_actual().
    '''

    def setUp(self):
        '''
        '''
        super(TestCorsMethods, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = SimpleHandler(self.get_app(), request, type_name='century')

    def test_actual_1(self):
        '''
        Origin request header is missing. No response headers are added.
        '''
        assert 'Origin' not in self.handler.request.headers  # pre-condition
        self.handler._cors_actual()
        assert 'Access-Control-Allow-Origin' not in self.handler._headers
        assert 'Vary' not in self.handler._headers
        assert 'Access-Control-Expose-Headers' not in self.handler._headers

    def test_actual_2(self):
        '''
        Origin request header is not in cors_allow_origin. No response headers are added.
        '''
        self.handler.request.headers['Origin'] = 'https://cantus_schmantus.org/'
        self.handler._cors_actual()
        assert 'Access-Control-Allow-Origin' not in self.handler._headers
        assert 'Vary' not in self.handler._headers
        assert 'Access-Control-Expose-Headers' not in self.handler._headers

    def test_actual_3a(self):
        '''
        Origin request header is in cors_allow_origin, which is a string. Response headers are added.
        '''
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        exp_expose_headers = bytes(','.join(abbot.CANTUS_RESPONSE_HEADERS), encoding='utf-8')

        self.handler._cors_actual()

        assert self.handler._headers['Access-Control-Allow-Origin'] == bytes(origin, encoding='utf-8')
        assert self.handler._headers['Vary'] == b'Origin'
        assert self.handler._headers['Access-Control-Expose-Headers'] == exp_expose_headers

    def test_actual_3b(self):
        '''
        Same as test_actual_3a() except "cors_allow_origin" is a space-separated list of values.
        '''
        self._simple_options.cors_allow_origin = 'http://one.ca http://two.ca'
        self.handler.request.headers['Origin'] = 'http://two.ca'
        exp_expose_headers = bytes(','.join(abbot.CANTUS_RESPONSE_HEADERS), encoding='utf-8')

        self.handler._cors_actual()

        assert self.handler._headers['Access-Control-Allow-Origin'] == b'http://two.ca'
        assert self.handler._headers['Vary'] == b'Origin'
        assert self.handler._headers['Access-Control-Expose-Headers'] == exp_expose_headers

    def test_actual_4(self):
        '''
        Origin request header is in cors_allow_origin, which is a list. Response headers are added.
        '''
        origin = 'website'
        self._simple_options.cors_allow_origin = ['debsite', 'website', 'zebsite']
        self.handler.request.headers['Origin'] = origin
        exp_expose_headers = bytes(','.join(abbot.CANTUS_RESPONSE_HEADERS), encoding='utf-8')

        self.handler._cors_actual()

        assert self.handler._headers['Access-Control-Allow-Origin'] == bytes(origin, encoding='utf-8')
        assert self.handler._headers['Vary'] == b'Origin'
        assert self.handler._headers['Access-Control-Expose-Headers'] == exp_expose_headers

    def test_preflight_1(self):
        '''
        Origin request header is missing. No repsonse headers are added.
        '''
        assert 'Origin' not in self.handler.request.headers  # pre-condition
        exp_missing_headers = ('Access-Control-Allow-Origin', 'Vary', 'Access-Control-Max-Age',
            'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers')

        self.handler._cors_preflight()

        for header in exp_missing_headers:
            assert header not in self.handler._headers

    def test_preflight_2(self):
        '''
        Origin request header is not in cors_allow_origin. No repsonse headers are added.
        '''
        self.handler.request.headers['Origin'] = 'https://cantus_schmantus.org/'
        exp_missing_headers = ('Access-Control-Allow-Origin', 'Vary', 'Access-Control-Max-Age',
            'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers')

        self.handler._cors_preflight()

        for header in exp_missing_headers:
            assert header not in self.handler._headers

    def test_preflight_3(self):
        '''
        Origin request header is correct, but Access-Control-Request-Method is missing.
        No repsonse headers are added.
        '''
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        assert 'Access-Control-Request-Method' not in self.handler.request.headers  # precondition
        exp_missing_headers = ('Access-Control-Allow-Origin', 'Vary', 'Access-Control-Max-Age',
            'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers')

        self.handler._cors_preflight()

        for header in exp_missing_headers:
            assert header not in self.handler._headers

    def test_preflight_4(self):
        '''
        Origin request header is correct, and Access-Control-Request-Method is not valid.
        No repsonse headers are added.
        '''
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        self.handler.request.headers['Access-Control-Request-Method'] = 'DELETE'
        exp_missing_headers = ('Access-Control-Allow-Origin', 'Vary', 'Access-Control-Max-Age',
            'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers')

        self.handler._cors_preflight()

        for header in exp_missing_headers:
            assert header not in self.handler._headers

    def test_preflight_5(self):
        '''
        - Origin request header is correct,
        - Access-Control-Request-Method is valid,
        - Access-Control-Request-Headers contains an invalid value
        No repsonse headers are added.
        '''
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        self.handler.request.headers['Access-Control-Request-Method'] = 'GET'
        self.handler.request.headers['Access-Control-Request-Headers'] = 'Retry-After'
        exp_missing_headers = ('Access-Control-Allow-Origin', 'Vary', 'Access-Control-Max-Age',
            'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers')

        self.handler._cors_preflight()

        for header in exp_missing_headers:
            assert header not in self.handler._headers

    def test_preflight_6(self):
        '''
        - Origin request header is correct,
        - Access-Control-Request-Method is valid,
        - Access-Control-Request-Headers is empty.
        All repsonse headers are added.
        '''
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        self.handler.request.headers['Access-Control-Request-Method'] = 'GET'

        self.handler._cors_preflight()

        assert self.handler._headers['Access-Control-Allow-Origin'] == bytes(origin, encoding='utf-8')
        assert self.handler._headers['Vary'] == b'Origin'
        assert self.handler._headers['Access-Control-Max-Age'] == b'86400'
        assert self.handler._headers['Access-Control-Allow-Methods'] == b'GET'
        assert 'Access-Control-Allow-Headers' not in self.handler._headers

    def test_preflight_7(self):
        '''
        - Origin request header is correct,
        - Access-Control-Request-Method is valid,
        - Access-Control-Request-Headers has some Cantus-API-specific headers
        All repsonse headers are added.
        '''
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        self.handler.request.headers['Access-Control-Request-Method'] = 'GET'
        self.handler.request.headers['Access-Control-Request-Headers'] = 'x-cantus-page,X-CANTUS-SORT'

        self.handler._cors_preflight()

        assert self.handler._headers['Access-Control-Allow-Origin'] == bytes(origin, encoding='utf-8')
        assert self.handler._headers['Vary'] == b'Origin'
        assert self.handler._headers['Access-Control-Max-Age'] == b'86400'
        assert self.handler._headers['Access-Control-Allow-Methods'] == b'GET'
        assert self.handler._headers['Access-Control-Allow-Headers'] == b'x-cantus-page,X-CANTUS-SORT'

    def test_preflight_8(self):
        '''
        test_preflight_7() with Access-Control-Request-Headers that includes some of what CORS calls
        "simple headers."
        '''
        request_headers = 'accept, content-type, x-cantus-page, x-cantus-per-page'
        expected = b'accept,content-type,x-cantus-page,x-cantus-per-page'
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        self.handler.request.headers['Access-Control-Request-Method'] = 'GET'
        self.handler.request.headers['Access-Control-Request-Headers'] = request_headers

        self.handler._cors_preflight()

        assert self.handler._headers['Access-Control-Allow-Headers'] == expected

    def test_preflight_9(self):
        '''
        test_preflight_7() with Access-Control-Request-Headers that includes some of what CORS calls
        "simple headers."
        '''
        request_headers = 'origin, x-requested-with'
        expected = b'origin,x-requested-with'
        origin = self._simple_options.cors_allow_origin
        self.handler.request.headers['Origin'] = origin
        self.handler.request.headers['Access-Control-Request-Method'] = 'GET'
        self.handler.request.headers['Access-Control-Request-Headers'] = request_headers

        self.handler._cors_preflight()

        assert self.handler._headers['Access-Control-Allow-Headers'] == expected
