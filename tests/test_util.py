#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_util.py
# Purpose:                Tests for abbot/util.py of the Abbot server.
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
Tests for abbot/util.py of the Abbot server.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock, TestCase
import pytest
from tornado import gen, testing, web
import parsimonious
import pysolrtornado

from hypothesis import assume, given, strategies as strats
import pytest

from abbot import __main__ as main
from abbot import util
import shared


class TestSingularResourceToPlural(TestCase):
    '''
    Tests for abbot.util.singular_resource_to_plural().
    '''

    def test_singular_resource_to_plural_1(self):
        "When the singular form has a corresponding pural."
        assert 'feasts' == util.singular_resource_to_plural('feast')

    @given(strats.text())
    def test_singular_resource_to_plural_2(self, convert_me):
        "When the singular form doesn't have a corresponding plural."
        # It's possible to get things that will convert, but unlikely... except for '*'
        assume('*' != convert_me)
        self.assertIsNone(util.singular_resource_to_plural(convert_me))


class TestSolrAskers(shared.TestHandler):
    '''
    Tests for abbot.util.ask_solr_by_id() and search_solr().
    '''

    @mock.patch('abbot.util.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_search_solr_1(self, mock_solr):
        "Basic test (no 'extra_params')."
        query = 'searching for this'
        expected = 'search results'
        mock_solr.search.return_value = shared.make_future(expected)
        actual = yield util.search_solr(query)
        assert expected == actual
        util.SOLR.search.assert_called_once_with(query, df='default_search')

    @mock.patch('abbot.util.SOLR', spec_set=pysolrtornado.Solr)
    @testing.gen_test
    def test_search_solr_2(self, mock_solr):
        "Basic test (with 'start', 'rows', and 'sort' kwargs)."
        query = 'searching for this'
        expected = 'search results'
        mock_solr.search.return_value = shared.make_future(expected)
        actual = yield util.search_solr(query, start=5, rows=50, sort='lol')
        assert expected == actual
        util.SOLR.search.assert_called_once_with(query, df='default_search', start=5, rows=50, sort='lol')

    @mock.patch('abbot.util.search_solr')
    @testing.gen_test
    def test_ask_solr_by_id_1(self, mock_search):
        "Ensure everything gets passed to search_solr()."
        expected = 'search results'
        mock_search.return_value = shared.make_future(expected)
        actual = yield util.ask_solr_by_id('genre', '162', start=1, rows=2, sort=3)
        assert expected == actual
        mock_search.assert_called_with('+type:genre +id:162', start=1, rows=2, sort=3)


class TestFormattedSorts(TestCase):
    '''
    Tests for abbot.util.prepare_formatted_sort() and abbot.util.postpare_formatted_sort().
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
    Tests for abbot.util.parse_fields_header().
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
    Tests for the abbot.util.request_wrapper decorator.
    '''

    def get_app(self):
        return web.Application(main.HANDLERS)

    def setUp(self):
        '''
        Make some additional mocks: log.error(); print().
        '''
        super(TestRequestWrapper, self).setUp()
        self._log_patcher = mock.patch('abbot.util.log')
        self._log = self._log_patcher.start()
        self._actual_print = __builtins__['print']
        __builtins__['print'] = mock.MagicMock()
        self._options_patcher = mock.patch('abbot.util.options')
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


class TestParseQuery(TestCase):
    '''
    Tests for util.parse_query().
    '''

    def test_basics(self):
        '''
        Basics:
        - can it differentiate fields?
        - same with some accented characters?
        - can it differentiate default and named fields?
        - can it deal with quoted field values?
        - can it deal with a single field?
        - can it deal with several fields?
        '''
        actual = util.parse_query('antiphon')
        expected = [('default', 'antiphon')]
        assert expected == actual
        #
        actual = util.parse_query('ántìphÖn')
        expected = [('default', 'ántìphÖn')]
        assert expected == actual
        #
        actual = util.parse_query('genre:antiphon')
        expected = [('genre', 'antiphon')]
        assert expected == actual
        #
        actual = util.parse_query('"in taberna" genre:antiphon')
        expected = [('default', '"in taberna"'), ('genre', 'antiphon')]
        assert expected == actual
        # Invalid: named field doesn't have a value.
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('size: drink:Dunkelweiß')
        assert util._INVALID_QUERY in str(excinfo.value)

    def test_wildcards(self):
        '''
        Wildcards:
        - both * and ?
        - can it deal with a single wildcard?
        - does it say consecutive * is invalid?
        - does it accept consecutive ?
        '''
        actual = util.parse_query('"in *" genre:*phon')
        expected = [('default', '"in *"'), ('genre', '*phon')]
        assert expected == actual
        # Invalid: consecutive * wildcards.
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('drink:Dunkel**')
        assert util._INVALID_QUERY in str(excinfo.value)
        #
        actual = util.parse_query('"in ?" genre:?phon')
        expected = [('default', '"in ?"'), ('genre', '?phon')]
        assert expected == actual
        #
        actual = util.parse_query('genre:???iphon')
        expected = [('genre', '???iphon')]
        assert expected == actual


class TestQueryParserSync(TestCase):
    '''
    Tests for the synchronous (non-coroutine) SEARCH request query-string parsing functions except
    util.parse_query().
    '''

    def test_collect_terms_1(self):
        '''
        Input looks like this:
        <query>
            <term A>
            <wonderful>
                <term B>
                <beautiful>
                    <term C>
                <term D>
            <meili>
            <perfect>
                <term E>
        '''
        term_a = parsimonious.nodes.Node('term', 'A', 0, 1)
        term_b = parsimonious.nodes.Node('term', 'B', 0, 1)
        term_c = parsimonious.nodes.Node('term', 'C', 0, 1)
        term_d = parsimonious.nodes.Node('term', 'D', 0, 1)
        term_e = parsimonious.nodes.Node('term', 'E', 0, 1)
        beautiful = parsimonious.nodes.Node('beautiful', '', 0, 1, [term_c])
        wonderful = parsimonious.nodes.Node('wonderful', '', 0, 1, [term_b, beautiful, term_d])
        meili = parsimonious.nodes.Node('meili', '', 0, 1)
        perfect = parsimonious.nodes.Node('perfect', '', 0, 1, [term_e])
        query = parsimonious.nodes.Node('query', '', 0, 1, [term_a, wonderful, meili, perfect])

        expected = [term_a, term_b, term_c, term_d, term_e]
        actual = util._collect_terms(query)
        assert expected == actual

    def test_collect_terms_2(self):
        '''
        Input looks like this:
        <query>
            <wonderful>
                <beautiful>
            <meili>
            <perfect>
        '''
        beautiful = parsimonious.nodes.Node('beautiful', '', 0, 1)
        wonderful = parsimonious.nodes.Node('wonderful', '', 0, 1, [beautiful])
        meili = parsimonious.nodes.Node('meili', '', 0, 1)
        perfect = parsimonious.nodes.Node('perfect', '', 0, 1)
        query = parsimonious.nodes.Node('query', '', 0, 1, [wonderful, meili, perfect])

        expected = []
        actual = util._collect_terms(query)
        assert expected == actual

    def test_collect_terms_3(self):
        '''
        Input looks like this:
        <term A>
        '''
        root = parsimonious.nodes.Node('term', 'A', 0, 1)
        expected = [root]
        actual = util._collect_terms(root)
        assert expected == actual

    def test_assemble_query_1(self):
        '''
        With a single query component.
        '''
        components = [('feast_id', '123')]
        expected = 'feast_id:123'
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_2(self):
        '''
        With several query components.
        '''
        components = [('feast_id', '123'), ('name', '"Danceathon Smith"')]
        expected = 'feast_id:123 AND name:"Danceathon Smith"'
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_3(self):
        '''
        With a single query component with the "default" field.
        '''
        components = [('default', '"Deus Rex"')]
        expected = '"Deus Rex"'
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_4(self):
        '''
        With several query components, including some with the "default" field.
        '''
        components = [('feast_id', '123'), ('name', '"Danceathon Smith"'), ('default', '"Deus Rex"')]
        expected = 'feast_id:123 AND name:"Danceathon Smith" AND "Deus Rex"'
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)


class TestQueryParserAsync(shared.TestHandler):
    '''
    Tests for the asynchronous (coroutine) SEARCH request query-string parsing functions.
    '''

    @mock.patch('abbot.util.search_solr')
    @testing.gen_test
    def test_run_subqueries_1(self, mock_ask_solr):
        '''
        With a single cross-referenced field that has a single result.
        '''

        mock_solr_response = shared.make_results([{'id': '123', 'name': 'antiphon', 'type': 'genre'}])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        components = [('genre', 'antiphon')]
        expected = [('genre_id', '123')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)
        mock_ask_solr.assert_called_once_with('type:genre AND (antiphon)')

    @mock.patch('abbot.util.search_solr')
    @testing.gen_test
    def test_run_subqueries_2(self, mock_ask_solr):
        '''
        With a single cross-referenced field with three results.
        '''

        mock_solr_response = shared.make_results([{'id': '123', 'name': 'antiphon', 'type': 'genre'},
                                                  {'id': '124', 'name': 'bantiphon', 'type': 'genre'},
                                                  {'id': '125', 'name': 'cantiphon', 'type': 'genre'}
        ])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        components = [('genre', 'antiphon')]
        expected = [('default', '(genre_id:123^3 OR genre_id:124^2 OR genre_id:125^1)')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)
        mock_ask_solr.assert_called_once_with('type:genre AND (antiphon)')

    @mock.patch('abbot.util.search_solr')
    @testing.gen_test
    def test_run_subqueries_3(self, mock_ask_solr):
        '''
        With a cross-referenced field (with a single result) and another field.
        '''

        mock_solr_response = shared.make_results([{'id': '123', 'name': 'antiphon', 'type': 'genre'}])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        components = [('name', 'Jeffrey'), ('genre', 'antiphon')]
        expected = [('name', 'Jeffrey'), ('genre_id', '123')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)
        mock_ask_solr.assert_called_once_with('type:genre AND (antiphon)')

    @mock.patch('abbot.util.search_solr')
    @testing.gen_test
    def test_run_subqueries_4(self, mock_ask_solr):
        '''
        With two cross-referenced fields and two other fields.
        '''

        # complex bit to have two different results returned
        response_genre = shared.make_results([{'id': '123', 'name': 'antiphon', 'type': 'genre'}])
        response_genre = shared.make_future(response_genre)
        response_feast = shared.make_results([{'id': '1474', 'name': 'Ad Magnificat', 'type': 'feast'},
                                              {'id': '1499', 'name': 'Ad Subtrac', 'type': 'feast'}])
        response_feast = shared.make_future(response_feast)
        def returner(query):
            if 'genre' in query:
                return response_genre
            else:
                return response_feast
        mock_ask_solr.side_effect = returner
        #
        components = [('genre', 'antiphon'), ('differentia', '3'), ('folio', '001r'),
                      ('feast', 'magnificat')]
        expected = [('genre_id', '123'), ('differentia', '3'), ('folio', '001r'),
                    ('default', '(feast_id:1474^2 OR feast_id:1499^1)')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)
        mock_ask_solr.assert_any_call('type:genre AND (antiphon)')
        mock_ask_solr.assert_any_call('type:feast AND (magnificat)')

    @mock.patch('abbot.util.search_solr')
    @testing.gen_test
    def test_run_subqueries_5(self, mock_ask_solr):
        '''
        With no cross-referenced fields.
        '''

        mock_solr_response = shared.make_results([{'id': '123', 'name': 'antiphon', 'type': 'genre'}])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        components = [('name', 'Jeffrey')]
        expected = [('name', 'Jeffrey')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mock_ask_solr.call_count)

    @mock.patch('abbot.util.search_solr')
    @testing.gen_test
    def test_run_subqueries_6(self, mock_ask_solr):
        '''
        With a single cross-referenced field that has no results.
        '''

        mock_solr_response = shared.make_results([])
        mock_ask_solr.return_value = shared.make_future(mock_solr_response)
        components = [('genre', 'antiphon')]

        # we have to do this a weird way, because you can't "yield" in assertRaises()
        try:
            yield util.run_subqueries(components)
        except util.InvalidQueryError:
            mock_ask_solr.assert_called_once_with('type:genre AND (antiphon)')
        else:
            raise AssertionError('InvalidQueryError not raised')
