#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_util.py
# Purpose:                Tests for abbott/util.py of the Abbott server.
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
Tests for abbott/util.py of the Abbott server.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock, TestCase
import pytest
from tornado import gen, testing, web
import pysolrtornado

from abbott import __main__ as main
from abbott import util
import shared


class TestSingularResourceToPlural(TestCase):
    '''
    Tests for abbott.util.singular_resource_to_plural().
    '''

    def test_singular_resource_to_plural_1(self):
        "When the singular form has a corresponding pural."
        self.assertEqual('cantusids', util.singular_resource_to_plural('cantusid'))

    def test_singular_resource_to_plural_2(self):
        "When the singular form doesn't have a corresponding plural."
        self.assertIsNone(util.singular_resource_to_plural('automobiles'))


class TestAskSolrById(shared.TestHandler):
    '''
    Tests for abbott.util.ask_solr_by_id().
    '''

    @mock.patch('abbott.util.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_ask_solr_by_id_1(self, mock_solr):
        "Basic test."
        mock_solr.search.return_value = shared.make_future('search results')
        expected = 'search results'
        actual = yield util.ask_solr_by_id('genre', '162')
        self.assertEqual(expected, actual)
        util.SOLR.search.assert_called_once_with('+type:genre +id:162')

    @mock.patch('abbott.util.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_ask_solr_by_id_2(self, mock_solr):
        "with 'start' and 'rows' kwargs"
        mock_solr.search.return_value = shared.make_future('search results')
        expected = 'search results'
        actual = yield util.ask_solr_by_id('genre', '162', start=5, rows=50)
        self.assertEqual(expected, actual)
        util.SOLR.search.assert_called_once_with('+type:genre +id:162', start=5, rows=50)

    @mock.patch('abbott.util.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_ask_solr_by_id_3(self, mock_solr):
        "with 'rows' and 'sort' kwargs"
        mock_solr.search.return_value = shared.make_future('search results')
        expected = 'search results'
        actual = yield util.ask_solr_by_id('genre', '162', rows=42, sort='incipit asc')
        self.assertEqual(expected, actual)
        util.SOLR.search.assert_called_once_with('+type:genre +id:162', rows=42, sort='incipit asc')


class TestFormattedSorts(TestCase):
    '''
    Tests for abbott.util.prepare_formatted_sort() and abbott.util.postpare_formatted_sort().
    '''

    def test_prepare_sort_1(self):
        '''
        - works when there are a bunch of spaces all over
        '''
        sort = '  incipit  ,   asc'
        expected = 'incipit asc'
        actual = util.prepare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_prepare_sort_2(self):
        '''
        - works when there are many field specs
        '''
        sort = 'incipit, asc; feast,desc; family_name, asc   '
        expected = 'incipit asc,feast_id desc,family_name asc'
        actual = util.prepare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_prepare_sort_3(self):
        '''
        - ValueError when disallowed character
        '''
        sort = 'incipit~,asc'
        self.assertRaises(ValueError, util.prepare_formatted_sort, sort)

    def test_prepare_sort_4(self):
        '''
        - ValueError when no direction
        '''
        sort = 'incipit'
        self.assertRaises(ValueError, util.prepare_formatted_sort, sort)

    def test_prepare_sort_5(self):
        '''
        - ValueError when misspelled direction
        '''
        sort = 'incipit,dasc'
        self.assertRaises(ValueError, util.prepare_formatted_sort, sort)

    def test_prepare_sort_6(self):
        '''
        - KeyError when field isn't in the approved list
        '''
        sort = 'password,asc'
        self.assertRaises(KeyError, util.prepare_formatted_sort, sort)

    def test_postpare_sort_1(self):
        '''
        - with a single field
        '''
        sort = 'incipit asc'
        expected = 'incipit,asc'
        actual = util.postpare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_postpare_sort_2(self):
        '''
        - with several fields
        '''
        sort = 'incipit asc,id desc,family_name asc'
        expected = 'incipit,asc;id,desc;family_name,asc'
        actual = util.postpare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_postpare_sort_3(self):
        '''
        - with several fields and lots of unnecessary spaces
        '''
        sort = '   incipit     asc  ,       id    desc   ,    family_name    asc     '
        expected = 'incipit,asc;id,desc;family_name,asc'
        actual = util.postpare_formatted_sort(sort)
        self.assertEqual(expected, actual)


class TestParseFieldsHeader(TestCase):
    '''
    Tests for abbott.util.parse_fields_header().
    '''
    # TODO: make these parameterized

    def test_empty(self):
        "the header is empty (should return ['id'])"
        header_val = ''
        returned_fields = ['name', 'style']
        expected = ['id', 'type']
        actual = util.parse_fields_header(header_val, returned_fields)
        self.assertCountEqual(expected, actual)

    def test_all(self):
        "when header_val says to return everything in returned_fields"
        header_val = 'name,style'
        returned_fields = ['name', 'style']
        expected = ['id', 'type', 'name', 'style']
        actual = util.parse_fields_header(header_val, returned_fields)
        self.assertCountEqual(expected, actual)

    def test_fewer(self):
        "when 'name' isn't in header_val it shouldn't be returned"
        header_val = 'style'
        returned_fields = ['name', 'style']
        expected = ['id', 'type', 'style']
        actual = util.parse_fields_header(header_val, returned_fields)
        self.assertCountEqual(expected, actual)

    def test_lotsa_spaces(self):
        "extra spaces shouldn't prevent correct return"
        header_val = '     style     ,      name       '
        returned_fields = ['name', 'style']
        expected = ['id', 'type', 'name', 'style']
        actual = util.parse_fields_header(header_val, returned_fields)
        self.assertCountEqual(expected, actual)

    def test_id_missing(self):
        "when 'id' is given, it should still be returned just once"
        header_val = 'name,id'
        returned_fields = ['name', 'style']
        expected = ['id', 'type', 'name']
        actual = util.parse_fields_header(header_val, returned_fields)
        self.assertCountEqual(expected, actual)

    def test_invalid_field(self):
        "when one of the fields in header_val isn't in returned_fields it should raise ValueError"
        header_val = 'id, type, price'
        returned_fields = ['name', 'style']
        with pytest.raises(ValueError) as excinfo:
            util.parse_fields_header(header_val, returned_fields)
        self.assertEqual(util._INVALID_FIELD_NAME.format('price'), excinfo.value.args[0])

    def test_id_suffixed_field(self):
        '''
        One of the fields in header_val corresponds to a field with an "_id" suffix in
        returned_fields. This is like when users specify "genre" instead of "genre_id" in the header,
        which is what we expect users to do, but because we manage this with self.returned_fields
        it must be the _id suffixed version that we return.
        '''
        header_val = 'name,style,product'
        returned_fields = ['name', 'style', 'product_id']
        expected = ['id', 'type', 'name', 'style', 'product_id']
        actual = util.parse_fields_header(header_val, returned_fields)
        self.assertCountEqual(expected, actual)


class TestDoDictTransfer(TestCase):
    "Tests for util.do_dict_transfer()."

    def test_all_keys(self):
        '''
        All keys in "translations" appear in "from_here."
        '''
        from_here = {'a': 1, 'c': 2, 'e': 3}
        translations = (('a', 'b'), ('c', 'd'), ('e', 'f'))
        expected = {'b': 1, 'd': 2, 'f': 3}
        actual = util.do_dict_transfer(from_here, translations)
        self.assertEqual(expected, actual)

    def test_no_keys(self):
        '''
        No keys in "translations" appear in "from_here."
        '''
        from_here = {'z': 1, 'y': 2}
        translations = (('a', 'b'), ('c', 'd'), ('e', 'f'))
        expected = {}
        actual = util.do_dict_transfer(from_here, translations)
        self.assertEqual(expected, actual)

    def test_some_keys(self):
        '''
        Some keys in "translations" appear in "from_here."
        '''
        from_here = {'a': 1, 'c': 2}
        translations = (('a', 'b'), ('c', 'd'), ('e', 'f'))
        expected = {'b': 1, 'd': 2}
        actual = util.do_dict_transfer(from_here, translations)
        self.assertEqual(expected, actual)

    def test_empty_from_here(self):
        '''
        There are no keys in "from_here."
        '''
        from_here = {}
        translations = (('a', 'b'), ('c', 'd'))
        expected = {}
        actual = util.do_dict_transfer(from_here, translations)
        self.assertEqual(expected, actual)


class TestRequestWrapper(testing.AsyncHTTPTestCase):
    '''
    Tests for the abbott.util.request_wrapper decorator.
    '''

    def get_app(self):
        return web.Application(main.HANDLERS)

    def setUp(self):
        '''
        Make some additional mocks: log.error(); print().
        '''
        super(TestRequestWrapper, self).setUp()
        self._log_patcher = mock.patch('abbott.util.log')
        self._log = self._log_patcher.start()
        self._actual_print = __builtins__['print']
        __builtins__['print'] = mock.MagicMock()
        self._options_patcher = mock.patch('abbott.util.options')
        self._options = self._options_patcher.start()
        self._options.debug = False

    def tearDown(self):
        '''
        Remove the mock from the global "options" modules.
        '''
        __builtins__['print'] = self._actual_print
        self._log_patcher.stop()
        self._options_patcher.stop()
        super(TestRequestWrapper, self).tearDown()

    @testing.gen_test
    def test_success(self):
        '''
        - everything works fine
        - none of those things called
        '''

        # set up a handler
        class SomeHandler(web.RequestHandler):
            def __init__(self):
                pass

            @util.request_wrapper
            @gen.coroutine
            def get(self):
                self.write('five')

            write = mock.MagicMock()
            send_error = mock.MagicMock()

        # run the test
        some = SomeHandler()
        actual = yield some.get()

        # check
        self.assertIsNone(actual)
        some.write.assert_called_once_with('five')
        self.assertEqual(0, print.call_count)
        self.assertEqual(0, self._log.error.call_count)
        self.assertEqual(0, some.send_error.call_count)

    @testing.gen_test
    def test_nodebug_failure(self):
        '''
        - func() raises IndexError; debug is True
        - print() called with the message
        - self.send_error(500, reason='Programmer Error')
        '''

        self._options.debug = True

        # set up a handler
        class SomeHandler(web.RequestHandler):
            def __init__(self):
                pass

            @util.request_wrapper
            @gen.coroutine
            def get(self):
                self.write('five')

            write = mock.MagicMock(side_effect=IndexError)
            send_error = mock.MagicMock()

        # run the test
        some = SomeHandler()
        actual = yield some.get()

        # check
        self.assertIsNone(actual)
        some.write.assert_called_once_with('five')
        self.assertEqual(1, print.call_count)
        self.assertEqual(0, self._log.error.call_count)
        some.send_error.assert_called_once_with(500, reason='Programmer Error')

    @testing.gen_test
    def test_debug_wrong_order(self):
        '''
        - func() is wrapped in the wrong order; debug is False
        - log.error() called with the message
        - the message ends with 'IMPORTANT: write the @request_wrapper decorator above @gen.coroutine'
        - self.send_error(500, reason='Programmer Error')
        '''

        # set up a handler
        class SomeHandler(web.RequestHandler):
            def __init__(self):
                pass

            @gen.coroutine
            @util.request_wrapper
            def get(self):
                self.write('five')

            write = mock.MagicMock()
            send_error = mock.MagicMock()

        # run the test
        exp_log_ending = 'IMPORTANT: write the @request_wrapper decorator above @gen.coroutine'
        some = SomeHandler()
        actual = yield some.get()

        # check
        # self.assertIsNone(actual)
        some.write.assert_called_once_with('five')
        self.assertEqual(0, print.call_count)
        self.assertEqual(1, self._log.error.call_count)
        self.assertTrue(self._log.error.call_args[0][0].endswith(exp_log_ending))
        some.send_error.assert_called_once_with(500, reason='Programmer Error')
