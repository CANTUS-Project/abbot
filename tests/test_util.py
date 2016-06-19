#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_util.py
# Purpose:                Tests for abbot/util.py of the Abbot server.
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

    def test_singular_resource_to_plural_2(self):
        "When the singular form doesn't have a corresponding plural."
        with pytest.raises(KeyError):
            self.assertIsNone(util.singular_resource_to_plural('Franklin is a turtle.'))


class TestSolrAskers(shared.TestHandler):
    '''
    Tests for abbot.util.ask_solr_by_id() and search_solr().
    '''

    def setUp(self):
        super(TestSolrAskers, self).setUp()
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_search_solr_1(self):
        "Basic test (no 'extra_params')."
        query = 'searching for this'
        expected = {'a': 'search results'}
        self.solr.search_se.add(query, expected)
        actual = yield util.search_solr(query)
        assert [expected] == actual.docs
        self.solr.search.assert_called_with(query, df='default_search')

    @testing.gen_test
    def test_search_solr_2(self):
        "Basic test (with 'start', 'rows', and 'sort' kwargs)."
        query = 'searching for this'
        expected = {'a': 'search results'}
        self.solr.search_se.add(query, expected)
        actual = yield util.search_solr(query, start=5, rows=50, sort='lol')
        assert [expected] == actual.docs
        self.solr.search.assert_called_with(query, df='default_search', start=5, rows=50, sort='lol')

    @testing.gen_test
    def test_search_solr_3(self):
        '''
        When the "query" is empty, search_solr() shouldn't bother asking Solr, and should simply
        return an empty set of results.
        '''
        query = ''
        actual = yield util.search_solr(query)
        assert len(actual) == 0
        assert self.solr.search.call_count == 0

    @testing.gen_test
    def test_ask_solr_by_id_1(self):
        "Ensure everything gets passed to search_solr()."
        expected = {'a': 'search results'}
        self.solr.search_se.add('id:162', expected)
        actual = yield util.ask_solr_by_id('genre', '162', start=1, rows=2, sort=3)
        assert [expected] == actual.docs
        self.solr.search.assert_called_with('+type:genre +id:162', start=1, rows=2, sort=3,
            df='default_search')


class TestFormattedSorts(TestCase):
    '''
    Tests for abbot.util.prepare_formatted_sort() and abbot.util.postpare_formatted_sort().
    '''

    def test_prepare_sort_1(self):
        '''
        - works when there are a bunch of spaces all over
        '''
        sort = '  incipit  ;   asc'
        expected = 'incipit asc'
        actual = util.prepare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_prepare_sort_2(self):
        '''
        - works when there are many field specs
        '''
        sort = 'incipit; asc, feast;desc, family_name; asc   '
        expected = 'incipit asc,feast_id desc,family_name asc'
        actual = util.prepare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_prepare_sort_3(self):
        '''
        - ValueError when disallowed character
        '''
        sort = 'incipit~;asc'
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
        sort = 'incipit;dasc'
        self.assertRaises(ValueError, util.prepare_formatted_sort, sort)

    def test_prepare_sort_6(self):
        '''
        - KeyError when field isn't in the approved list
        '''
        sort = 'password;asc'
        self.assertRaises(KeyError, util.prepare_formatted_sort, sort)

    def test_postpare_sort_1(self):
        '''
        - with a single field
        '''
        sort = 'incipit asc'
        expected = 'incipit;asc'
        actual = util.postpare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_postpare_sort_2(self):
        '''
        - with several fields
        '''
        sort = 'incipit asc,id desc,family_name asc'
        expected = 'incipit;asc,id;desc,family_name;asc'
        actual = util.postpare_formatted_sort(sort)
        self.assertEqual(expected, actual)

    def test_postpare_sort_3(self):
        '''
        - with several fields and lots of unnecessary spaces
        '''
        sort = '   incipit     asc  ,       id    desc   ,    family_name    asc     '
        expected = 'incipit;asc,id;desc,family_name;asc'
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
        Put a mock on the "log" module.
        '''
        super(TestRequestWrapper, self).setUp()
        self._log_patcher = mock.patch('abbot.util.log')
        self._log = self._log_patcher.start()
        self._options_patcher = mock.patch('abbot.util.options')
        self._options = self._options_patcher.start()
        #
        self._options.debug = True

    def tearDown(self):
        '''
        Remove the mock from the global "options" modules.
        '''
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
        self.assertEqual(0, self._log.error.call_count)
        self.assertEqual(0, some.send_error.call_count)

    @testing.gen_test
    def test_request_failure_1(self):
        '''
        - func() raises IndexError
        - options.debug is True
        - log.debug() called with the message
        - self.send_error(500, reason='Programmer Error')
        '''

        # set up a handler
        self._options.debug = True
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
        some.send_error.assert_called_once_with(500, reason='Programmer Error')
        assert self._log.debug.call_count > 5
        # weird indexing on "call" objects is weird
        for each_call in self._log.debug.call_args_list:
            assert isinstance(each_call[0][0], str)
        assert 'Traceback' in self._log.debug.call_args_list[0][0][0]
        assert 'IndexError' in self._log.debug.call_args_list[-1][0][0]

    @testing.gen_test
    def test_request_failure_2(self):
        '''
        - func() raises IndexError
        - options.debug is False
        - log.debug() called with the message
        - self.send_error(500, reason='Programmer Error')
        '''

        # set up a handler
        self._options.debug = False
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
        some.send_error.assert_called_once_with(500, reason='Programmer Error')
        assert self._log.debug.call_count == 0

    @testing.gen_test
    def test_wrong_order(self):
        '''
        - func() is wrapped in the wrong order
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
        assert self._log.debug.call_count > 5
        assert self._log.error.call_count == 1
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

    def test_plus_and_minus(self):
        '''
        Boolean + and - and ! operators:
        - works before a named field
        - works after quoted field
        - works on the default field
        '''
        # plus
        actual = util.parse_query('+type:salad +name:Caesar')
        expected = ['+', ('type', 'salad'), '+', ('name', 'Caesar')]
        assert expected == actual
        #
        actual = util.parse_query('+type:"sal ad" +name:Caesar')
        expected = ['+', ('type', '"sal ad"'), '+', ('name', 'Caesar')]
        assert expected == actual
        #
        actual = util.parse_query('+type:salad +Caesar')
        expected = ['+', ('type', 'salad'), '+', ('default', 'Caesar')]
        assert expected == actual

        # minus
        actual = util.parse_query('-type:salad -name:Caesar')
        expected = ['-', ('type', 'salad'), '-', ('name', 'Caesar')]
        assert expected == actual
        #
        actual = util.parse_query('-type:"sal ad" -name:Caesar')
        expected = ['-', ('type', '"sal ad"'), '-', ('name', 'Caesar')]
        assert expected == actual
        #
        actual = util.parse_query('-type:salad -Caesar')
        expected = ['-', ('type', 'salad'), '-', ('default', 'Caesar')]
        assert expected == actual

        # exclamation
        actual = util.parse_query('!type:salad !name:Caesar')
        expected = ['!', ('type', 'salad'), '!', ('name', 'Caesar')]
        assert expected == actual
        #
        actual = util.parse_query('!type:"sal ad" !name:Caesar')
        expected = ['!', ('type', '"sal ad"'), '!', ('name', 'Caesar')]
        assert expected == actual
        #
        actual = util.parse_query('!type:salad !Caesar')
        expected = ['!', ('type', 'salad'), '!', ('default', 'Caesar')]
        assert expected == actual

    def test_boolean_infix(self):
        '''
        Boolean infix operators:
        - AND
        - OR
        - NOT
        - &&
        - ||
        '''
        actual = util.parse_query('soup OR salad')
        expected = [('default', 'soup'), 'OR', ('default', 'salad')]
        assert expected == actual
        #
        actual = util.parse_query('type:appetizer AND name:soup')
        expected = [('type', 'appetizer'), 'AND', ('name', 'soup')]
        assert expected == actual
        #
        actual = util.parse_query('type:appetizer AND NOT name:soup')
        expected = [('type', 'appetizer'), 'AND', 'NOT', ('name', 'soup')]
        assert expected == actual
        ####
        actual = util.parse_query('soup || salad')
        expected = [('default', 'soup'), '||', ('default', 'salad')]
        assert expected == actual
        #
        actual = util.parse_query('type:appetizer && name:soup')
        expected = [('type', 'appetizer'), '&&', ('name', 'soup')]
        assert expected == actual
        #
        actual = util.parse_query('type:appetizer && !name:soup')
        expected = [('type', 'appetizer'), '&&', '!', ('name', 'soup')]
        assert expected == actual

        # invalid queries
        #
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('AND branch')
        assert util._INVALID_QUERY in str(excinfo.value)
        #
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('quince OR')
        assert util._INVALID_QUERY in str(excinfo.value)
        #
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('jeremy ANDOR broccoli')
        assert util._INVALID_QUERY in str(excinfo.value)
        #
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('meal:lunch   NOTANDOR  &&  dish:pizza')
        assert util._INVALID_QUERY in str(excinfo.value)
        #
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('meal:lunch &&& dish:pizza')
        assert util._INVALID_QUERY in str(excinfo.value)
        #
        with pytest.raises(util.InvalidQueryError) as excinfo:
            util.parse_query('meal:lunch OR!dish:pizza')
        assert util._INVALID_QUERY in str(excinfo.value)

    def test_term_grouping_easy(self):
        '''
        Grouping a "term list" with single ( and ).
        '''
        actual = util.parse_query('(forcefield)')
        expected = ['(', ('default', 'forcefield'), ')']
        assert expected == actual
        #
        actual = util.parse_query('(force field)')
        expected = ['(', ('default', 'force'), ('default', 'field'), ')']
        assert expected == actual
        #
        actual = util.parse_query('(force OR field)')
        expected = ['(', ('default', 'force'), 'OR', ('default', 'field'), ')']
        assert expected == actual
        #
        actual = util.parse_query('force AND (field OR broccoli)')
        expected = [('default', 'force'), 'AND', '(', ('default', 'field'), 'OR', ('default', 'broccoli'), ')']
        assert expected == actual
        #
        actual = util.parse_query('(force && place:field) || (flavour:"ginger" && basis:"bread") NOT activity:baking')
        expected = [
            '(', ('default', 'force'), '&&', ('place', 'field'), ')',
            '||',
            '(', ('flavour', '"ginger"'), '&&', ('basis', '"bread"'), ')',
            'NOT',
            ('activity', 'baking')
        ]
        assert expected == actual
        #
        actual = util.parse_query('type:(chant OR feast)')
        expected = [
            ('type', ''),
            '(', ('default', 'chant'), 'OR', ('default', 'feast'), ')',
        ]
        assert expected == actual
        #
        actual = util.parse_query('+type:(name:feast OR name:chant)')
        expected = [
            '+', ('type', ''),
            '(', ('name', 'feast'), 'OR', ('name', 'chant'), ')'
        ]
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
                    <boolean_infix C>
                <term D>
            <meili>
            <perfect>
                <term E>
        '''
        term_a = parsimonious.nodes.Node('term', 'A', 0, 1)
        term_b = parsimonious.nodes.Node('term', 'B', 0, 1)
        bool_c = parsimonious.nodes.Node('boolean_infix', 'C', 0, 1)
        term_d = parsimonious.nodes.Node('term', 'D', 0, 1)
        term_e = parsimonious.nodes.Node('term', 'E', 0, 1)
        beautiful = parsimonious.nodes.Node('beautiful', '', 0, 1, [bool_c])
        wonderful = parsimonious.nodes.Node('wonderful', '', 0, 1, [term_b, beautiful, term_d])
        meili = parsimonious.nodes.Node('meili', '', 0, 1)
        perfect = parsimonious.nodes.Node('perfect', '', 0, 1, [term_e])
        query = parsimonious.nodes.Node('query', '', 0, 1, [term_a, wonderful, meili, perfect])

        expected = [term_a, term_b, bool_c, term_d, term_e]
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
        expected = 'feast_id:123 '
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_2(self):
        '''
        With several query components.
        '''
        components = [('feast_id', '123'), ('name', '"Danceathon Smith"')]
        expected = 'feast_id:123 name:"Danceathon Smith" '
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_3(self):
        '''
        With a single query component with the "default" field.
        '''
        components = [('default', '"Deus Rex"')]
        expected = '"Deus Rex" '
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_4(self):
        '''
        With several query components, including some with the "default" field.
        '''
        components = [('feast_id', '123'), ('name', '"Danceathon Smith"'), ('default', '"Deus Rex"')]
        expected = 'feast_id:123 name:"Danceathon Smith" "Deus Rex" '
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_5(self):
        '''
        With several query components and some "joining elements."
        '''
        components = ['+', ('feast_id', '123'), 'AND', '(', ('name', '"Danceathon Smith"'), 'OR',
            ('default', '"Deus Rex"'), ')']
        expected = ' +feast_id:123  AND  ( name:"Danceathon Smith"  OR "Deus Rex"  ) '
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_6(self):
        '''
        Complicated thing formed from this search query:

        '(force && full_text:field) || (provenance_id:"ginger" && siglum:"bread") NOT proofread_fulltext:baking'
        '''
        components = [
            '(', ('default', 'force'), '&&', ('full_text', 'field'), ')',
            '||',
            '(', ('provenance_id', '"ginger"'), '&&', ('siglum', '"bread"'), ')',
            'NOT',
            ('proofread_fulltext', 'baking')
        ]
        expected = ' ( force  && full_text:field  )  ||  ( provenance_id:"ginger"  && siglum:"bread"  )  NOT proofread_fulltext:baking '
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_7(self):
        '''
        Complicated thing formed from this search query:

        '+type:(name:feast OR name:chant)'
        '''
        components = [
            '+', ('type', ''),
            '(', ('name', 'feast'), 'OR', ('name', 'chant'), ')'
        ]
        # NB: you might not guess, but the extra spaces, even here, don't matter to Solr
        expected = ' +type:  ( name:feast  OR name:chant  ) '
        actual = util.assemble_query(components)
        self.assertEqual(expected, actual)

    def test_assemble_query_8(self):
        '''
        Complicated thing invalid fields.

        'flavour:"ginger" && basis:"bread"'
        '''
        components = [('flavour', '"ginger"'), '&&', ('basis', '"bread"')]
        with pytest.raises(ValueError) as excinfo:
            util.assemble_query(components)
        assert excinfo.value.the_field == 'flavour'

    def test_xref_group_1(self):
        '''
        It works with this query from the user:
            "century:(20th OR 21st)"
        '''
        components = [('century', ''), '(', ('default', '20th'), 'OR', ('default', '21st'), ')']
        start = 0
        expected = ('century:  ( 20th  OR 21st  ) ', 6)

        actual = util._make_xref_group(components, start)

        assert expected == actual

    def test_xref_group_2(self):
        '''
        It works with this query from the user:
            "incipit:deus* AND century:(20th OR 21st) AND genre:antiphon"
        '''
        components = [
            ('incipit', 'deus*'), 'AND',
            ('century', ''), '(', ('default', '20th'), 'OR', ('default', '21st'), ')',
            ('genre', 'antiphon')
        ]
        start = 2
        expected = ('century:  ( 20th  OR 21st  ) ', 6)

        actual = util._make_xref_group(components, start)

        assert expected == actual

    def test_xref_group_3(self):
        '''
        It works with this (admittedly nonsense) query from the user:
            "century:(20th OR (19th AND 21st) OR 18th)"
        '''
        components = [
            ('century', ''), '(',
            ('default', '20th'), 'OR', '(',
            ('default', '19th'), 'AND', ('default', '21st'), ')', 'OR',
            ('default', '18th'), ')'
        ]
        start = 0
        expected = ('century:  ( 20th  OR  ( 19th  AND 21st  )  OR 18th  ) ', 12)

        actual = util._make_xref_group(components, start)

        assert expected == actual

    def test_xref_group_4(self):
        '''
        It complains about this query from the user:
            "incipit:deus* AND century: ! 20th OR 21st) AND genre:antiphon"

        ... which should never get to this point anyway.
        '''
        components = [
            ('incipit', 'deus*'), 'AND',
            ('century', ''), '!', ('default', '20th'), 'OR', ('default', '21st'), ')',
            ('genre', 'antiphon')
        ]
        start = 2

        with pytest.raises(ValueError):
            actual = util._make_xref_group(components, start)

    def test_xref_group_5(self):
        '''
        It complains about this query from the user:
            "incipit:deus* AND century:(20th OR 21st AND genre:antiphon"

        ... which should never get to this point anyway.
        '''
        components = [
            ('incipit', 'deus*'), 'AND',
            ('century', ''), '(', ('default', '20th'), 'OR', ('default', '21st'),
            ('genre', 'antiphon')
        ]
        start = 2

        with pytest.raises(ValueError):
            actual = util._make_xref_group(components, start)

    def test_xref_group_6(self):
        '''
        It complains (properly) when it gets a "start" argument that's too large.

        ... which should never get to this point anyway.
        '''
        components = [
            ('incipit', 'deus*'), 'AND',
            ('century', ''), '(', ('default', '20th'), 'OR', ('default', '21st'),
            ('genre', 'antiphon')
        ]
        start = 40

        with pytest.raises(ValueError):
            actual = util._make_xref_group(components, start)


class TestQueryParserAsync(shared.TestHandler):
    '''
    Tests for the asynchronous (coroutine) SEARCH request query-string parsing functions.
    '''

    def setUp(self):
        super(TestQueryParserAsync, self).setUp()
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_run_subqueries_1(self):
        '''
        With a single cross-referenced field that has a single result.
        '''

        self.solr.search_se.add('type:genre', {'id': '123', 'name': 'antiphon', 'type': 'genre'})
        components = [('genre', 'antiphon')]
        expected = [('genre_id', '123')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_run_subqueries_2(self):
        '''
        With a single cross-referenced field with three results.
        '''

        self.solr.search_se.add('type:genre', {'id': '123', 'name': 'antiphon', 'type': 'genre'})
        self.solr.search_se.add('type:genre', {'id': '124', 'name': 'bantiphon', 'type': 'genre'})
        self.solr.search_se.add('type:genre', {'id': '125', 'name': 'cantiphon', 'type': 'genre'})
        components = [('genre', 'antiphon')]
        expected = [('default', '(genre_id:123^3 OR genre_id:124^2 OR genre_id:125^1)')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_run_subqueries_3(self):
        '''
        With a cross-referenced field (with a single result) and another field.
        '''

        self.solr.search_se.add('type:genre', {'id': '123', 'name': 'antiphon', 'type': 'genre'})
        components = [('name', 'Jeffrey'), ('genre', 'antiphon')]
        expected = [('name', 'Jeffrey'), ('genre_id', '123')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_run_subqueries_4(self):
        '''
        With two cross-referenced fields and two other fields.
        '''

        # complex bit to have two different results returned
        self.solr.search_se.add('type:genre', {'id': '123', 'name': 'antiphon', 'type': 'genre'})
        self.solr.search_se.add('type:feast', {'id': '1474', 'name': 'Ad Magnificat', 'type': 'feast'})
        self.solr.search_se.add('type:feast', {'id': '1499', 'name': 'Ad Subtrac', 'type': 'feast'})
        components = [('genre', 'antiphon'), ('differentia', '3'), ('folio', '001r'),
                      ('feast', 'magnificat')]
        expected = [('genre_id', '123'), ('differentia', '3'), ('folio', '001r'),
                    ('default', '(feast_id:1474^2 OR feast_id:1499^1)')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_run_subqueries_5(self):
        '''
        With no cross-referenced fields.
        '''
        components = [('name', 'Jeffrey')]
        expected = [('name', 'Jeffrey')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)
        assert 0 == self.solr.search.call_count

    @testing.gen_test
    def test_run_subqueries_6(self):
        '''
        With a single cross-referenced field that has no results.
        '''
        components = [('genre', 'antiphon')]
        with pytest.raises(util.InvalidQueryError) as excinfo:
            yield util.run_subqueries(components)
        self.solr.search.assert_called_with('type:genre AND (antiphon)', df='default_search')

    @testing.gen_test
    def test_run_subqueries_7(self):
        '''
        No cross-referenced fields, but there are two "joining elements."
        '''
        components = ['!', ('name', 'Jeffrey'), 'AND', ('occupation', 'composer')]
        expected = ['!', ('name', 'Jeffrey'), 'AND', ('occupation', 'composer')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)
        assert 0 == self.solr.search.call_count

    @testing.gen_test
    def test_run_subqueries_7(self):
        '''
        Several "joining elements" and a cross-referenced field.
        '''
        self.solr.search_se.add('type:genre', {'id': '666', 'type': 'genre', 'name': 'composer'})
        components = ['!', ('name', 'Jeffrey'), 'AND', '(', ('genre', 'composer'), ')']
        expected = ['!', ('name', 'Jeffrey'), 'AND', '(', ('genre_id', '666'), ')']

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_run_subqueries_8(self):
        '''
        Complicated thing from this query:

            "incipit:deus* AND century:(20th OR 21st)"

        (Ensure the weird subquery works when it's at the end of the query).
        '''
        exp_subquery = 'century:  ( 20th  OR 21st  ) '
        self.solr.search_se.add(exp_subquery, {'id': '666', 'type': 'century'})
        self.solr.search_se.add(exp_subquery, {'id': '777', 'type': 'century'})
        components = [
            ('incipit', 'deus*'), 'AND',
            ('century', ''), '(', ('default', '20th'), 'OR', ('default', '21st'), ')'
        ]
        expected = [('incipit', 'deus*'), 'AND', ('default', '(century_id:666 OR century_id:777)')]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_run_subqueries_9(self):
        '''
        Complicated thing from this query:

            "incipit:deus* AND century:(20th OR 21st) AND genre:antiphon"

        (Ensure the weird subquery works when it's in the middle of the query).
        '''
        exp_subquery = 'century:  ( 20th  OR 21st  ) '
        self.solr.search_se.add(exp_subquery, {'id': '666', 'type': 'century'})
        self.solr.search_se.add(exp_subquery, {'id': '777', 'type': 'century'})
        self.solr.search_se.add('genre', {'id': '4567', 'type': 'genre'})
        components = [
            ('incipit', 'deus*'), 'AND',
            ('century', ''), '(', ('default', '20th'), 'OR', ('default', '21st'), ')',
            ('genre', 'antiphon')
        ]
        expected = [
            ('incipit', 'deus*'), 'AND',
            ('default', '(century_id:666 OR century_id:777)'),
            ('genre_id', '4567')
        ]

        actual = yield util.run_subqueries(components)

        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_run_subqueries_10(self):
        '''
        Complicated thing that returns no results, from this query:

            "incipit:deus* AND century:(20th OR 21st) AND genre:antiphon"

        (Ensure the weird subquery works when it's in the middle of the query).
        '''
        exp_subquery = 'century:  ( 20th  OR 21st  ) '
        components = [
            ('incipit', 'deus*'), 'AND',
            ('century', ''), '(', ('default', '20th'), 'OR', ('default', '21st'), ')',
            ('genre', 'antiphon')
        ]
        expected = [
            ('incipit', 'deus*'), 'AND',
            ('default', '(century_id:666 OR century_id:777)'),
            ('genre_id', '4567')
        ]

        with pytest.raises(util.InvalidQueryError):
            actual = yield util.run_subqueries(components)


class TestVerifyResourceId(object):
    '''
    Tests for util._verify_resource_id().
    '''

    @given(strats.lists(
        elements=strats.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890-_'),
        min_size=1,
        average_size=6,
        ))
    def test_valid_ids(self, res_id):
        res_id = ''.join(res_id)
        if res_id[0] == '-' or res_id[0] == '_' or res_id[-1] == '-' or res_id[-1] == '_':
            with pytest.raises(ValueError) as excinfo:
                util._verify_resource_id(res_id)
            assert util._INVALID_ID in str(excinfo.value)
        else:
            assert None is util._verify_resource_id(res_id)

    def test_star(self):
        "If the id is '*' that's okay too."
        assert None is util._verify_resource_id('*')

    def test_invalid_ids(self):
        "We need to make sure we test these every time."
        with pytest.raises(ValueError) as excinfo:
            util._verify_resource_id('')
        assert util._INVALID_ID in str(excinfo.value)
        #
        with pytest.raises(ValueError) as excinfo:
            util._verify_resource_id('-')
        assert util._INVALID_ID in str(excinfo.value)
        #
        with pytest.raises(ValueError) as excinfo:
            util._verify_resource_id('_-')
        assert util._INVALID_ID in str(excinfo.value)
        #
        with pytest.raises(ValueError) as excinfo:
            util._verify_resource_id('_ejlk2458')
        assert util._INVALID_ID in str(excinfo.value)
        #
        with pytest.raises(ValueError) as excinfo:
            util._verify_resource_id('e@e')
        assert util._INVALID_ID in str(excinfo.value)
        #
        with pytest.raises(ValueError) as excinfo:
            util._verify_resource_id('kjhlea!kljhtkjhe')
        assert util._INVALID_ID in str(excinfo.value)
