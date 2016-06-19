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
import pysolrtornado
from tornado import httpclient, testing
from abbot import __main__ as main
from abbot import complex_handler
ComplexHandler = complex_handler.ComplexHandler
Xref = complex_handler.Xref
import shared


class TestXref(shared.TestHandler):
    '''
    Tests for the static methods in the Xref class.
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestXref, self).setUp()
        request = httpclient.HTTPRequest(url='/zool/', method='GET')
        request.connection = mock.Mock()  # required for Tornado magic things
        self.handler = ComplexHandler(self.get_app(), request, type_name='source')

    def test_collect_1(self):
        "When the 'record' is empty."
        post, xref_query = Xref.collect({})
        assert post == {}
        assert xref_query == set([])

    def test_collect_2(self):
        "When the 'record' has only non-cross-referenced fields."
        record = {'id': '123', 'incipit': 'Deus rawr'}
        post, xref_query = Xref.collect(record)
        assert post == record
        assert xref_query == set([])

    def test_collect_3(self):
        "When the 'record' has a simple cross-reference (not a list)."
        record = {'id': '123', 'incipit': 'Deus rawr', 'feast_id': '666'}
        post, xref_query = Xref.collect(record)
        assert post == {'id': '123', 'incipit': 'Deus rawr'}
        assert xref_query == set(['id:666'])

    def test_collect_4(self):
        "When the 'record' has a list cross-reference."
        record = {'id': '123', 'incipit': 'Deus rawr', 'indexers': ['416', '905']}
        post, xref_query = Xref.collect(record)
        assert post == {'id': '123', 'incipit': 'Deus rawr'}
        assert isinstance(xref_query, set)
        self.assertCountEqual(xref_query, ['id:416', 'id:905'])

    def test_collect_5(self):
        "When the 'record' has a simple and a list cross-reference."
        record = {'id': '123', 'incipit': 'Deus rawr', 'indexers': ['416', '905'], 'feast_id': '666'}
        post, xref_query = Xref.collect(record)
        assert post == {'id': '123', 'incipit': 'Deus rawr'}
        assert isinstance(xref_query, set)
        self.assertCountEqual(xref_query, ['id:416', 'id:905', 'id:666'])

    def test_collect_6(self):
        "When the 'record' has a duplicate cross-reference."
        record = {'id': '123', 'incipit': 'Deus rawr', 'indexers': ['416', '905', '416']}
        post, xref_query = Xref.collect(record)
        assert post == {'id': '123', 'incipit': 'Deus rawr'}
        assert isinstance(xref_query, set)
        self.assertCountEqual(xref_query, ['id:416', 'id:905'])

    @testing.gen_test
    def test_lookup_1(self):
        "Returns an empty dictionary when the xref_query is an empty list."
        actual = yield Xref.lookup(set([]))
        assert actual == {}

    @testing.gen_test
    def test_lookup_2(self):
        "Returns an empty dictionary when the query returns no results."
        self.solr = self.setUpSolr()

        actual = yield Xref.lookup(set(['id:123']))

        assert actual == {}

    @testing.gen_test
    def test_lookup_3(self):
        "Returns a single-element dictionary when the query returns one result."
        self.solr = self.setUpSolr()
        self.solr.search_se.add('id:123', {'id': '123', 'display_name': 'Carte Blanche'})

        actual = yield Xref.lookup(set(['id:123']))

        assert actual == {'123': {'id': '123', 'display_name': 'Carte Blanche'}}

    @testing.gen_test
    def test_lookup_4(self):
        "Returns a three-element dictionary when the query returns three results."
        self.solr = self.setUpSolr()
        self.solr.search_se.add('id:123', {'id': '123', 'display_name': 'Carte Blanche'})
        self.solr.search_se.add('id:124', {'id': '124', 'display_name': 'Blarte Canche'})
        self.solr.search_se.add('id:125', {'id': '125', 'display_name': 'Shmarte Shmanche'})

        actual = yield Xref.lookup(set(['id:123', 'id:124', 'id:125']))

        assert actual == {
            '123': {'id': '123', 'display_name': 'Carte Blanche'},
            '124': {'id': '124', 'display_name': 'Blarte Canche'},
            '125': {'id': '125', 'display_name': 'Shmarte Shmanche'},
        }

    @testing.gen_test
    def test_lookup_5(self):
        "Submits the proper search query when there's one element in xref_query."
        self.solr = self.setUpSolr()

        yield Xref.lookup(set(['id:123']))

        self.solr.search.assert_called_with('id:123', df='default_search', rows=1)

    @testing.gen_test
    def test_lookup_6(self):
        "Submits the proper search query when there are three elements in xref_query."
        # NOTE: this test submits a list to lookup() rather than a set. That's because the order of
        #       a set is indeterminate, so the assertion would be MUCH more complicated.
        self.solr = self.setUpSolr()

        yield Xref.lookup(['id:123', 'id:124', 'id:125'])

        self.solr.search.assert_called_with('id:123 OR id:124 OR id:125', df='default_search', rows=3)

    @mock.patch('abbot.complex_handler.log.warn')
    @testing.gen_test
    def test_lookup_7(self, mock_warn):
        "Returns an empty dictionary when the Solr request produces a SolrError."
        self.solr = self.setUpSolr()
        self.solr.search = mock.Mock(side_effect=pysolrtornado.SolrError('test_lookup_7()'))

        actual = yield Xref.lookup(set(['id:123']))

        assert actual == {}
        assert mock_warn.call_count == 1
        assert mock_warn.call_args[0][0].endswith('test_lookup_7()')

    def test_fill_1(self):
        "Fills a single, non-list field."
        record = {'id': '123', 'feast_id': '5733'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}}
        expected = {'id': '123', 'feast': 'Thanksgiving'}

        actual = Xref.fill(record, result, xrefs)

        assert actual == expected

    def test_fill_2(self):
        "Fills a single field that's a list."
        record = {'id': '123', 'editors': ['444', '555']}
        result = {'id': '123'}
        xrefs = {'444': {'display_name': 'D. Smith'}, '555': {'display_name': 'F. Johnson'}}
        expected = {'id': '123', 'editors': ['D. Smith', 'F. Johnson']}

        actual = Xref.fill(record, result, xrefs)

        assert actual == expected

    def test_fill_3(self):
        "Fills several fields."
        record = {'id': '123', 'feast_id': '5733', 'editors': ['444', '555']}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}, '444': {'display_name': 'D. Smith'},
            '555': {'display_name': 'F. Johnson'}}
        expected = {'id': '123', 'feast': 'Thanksgiving', 'editors': ['D. Smith', 'F. Johnson']}

        actual = Xref.fill(record, result, xrefs)

        assert actual == expected

    def test_fill_4(self):
        "Leaves empty a field for which the cross-reference wasn't found."
        record = {'id': '123', 'feast_id': '5733', 'office_id': '9882'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}}
        expected = {'id': '123', 'feast': 'Thanksgiving'}

        actual = Xref.fill(record, result, xrefs)

        assert actual == expected

    def test_fill_5(self):
        "Still works when no cross-reference results were found."
        record = {'id': '123', 'feast_id': '5733'}
        result = {'id': '123'}
        xrefs = {}
        expected = {'id': '123'}

        actual = Xref.fill(record, result, xrefs)

        assert actual == expected

    def test_fill_6(self):
        "Still works when there are many more cross-references than needed in the resource."
        record = {'id': '123', 'feast_id': '5733'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}, '444': {'display_name': 'D. Smith'},
            '555': {'display_name': 'F. Johnson'}}
        expected = {'id': '123', 'feast': 'Thanksgiving'}

        actual = Xref.fill(record, result, xrefs)

        assert actual == expected

    def test_fill_7(self):
        "Still works when there are no fields to cross-reference."
        record = {'id': '123'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}}
        expected = {'id': '123'}

        actual = Xref.fill(record, result, xrefs)

        assert actual == expected

    def test_resources_1(self):
        "Fills a single, non-list field."
        record = {'id': '123', 'feast_id': '5733'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}}
        expected = {'feast_id': '5733', 'feast': 'https://cantus.org/feasts/5733/'}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    def test_resources_2(self):
        "Fills a single field that's a list."
        record = {'id': '123', 'editors': ['444', '555']}
        result = {'id': '123'}
        xrefs = {'444': {'display_name': 'D. Smith'}, '555': {'display_name': 'F. Johnson'}}
        expected = {'editors_id': ['444', '555'], 'editors': ['https://cantus.org/indexers/444/',
            'https://cantus.org/indexers/555/']}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    def test_resources_3(self):
        "Fills several fields."
        record = {'id': '123', 'feast_id': '5733', 'editors': ['444', '555']}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}, '444': {'display_name': 'D. Smith'},
            '555': {'display_name': 'F. Johnson'}}
        expected = {'feast_id': '5733', 'feast': 'https://cantus.org/feasts/5733/',
            'editors_id': ['444', '555'], 'editors': ['https://cantus.org/indexers/444/',
            'https://cantus.org/indexers/555/']}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    def test_resources_4a(self):
        "Leaves empty a field for which the cross-reference wasn't found (non-list not found)."
        record = {'id': '123', 'feast_id': '5733', 'office_id': '9882'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}}
        expected = {'feast_id': '5733', 'feast': 'https://cantus.org/feasts/5733/'}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    def test_resources_4b(self):
        "Leaves empty a field for which the cross-reference wasn't found (list not found)."
        record = {'id': '123', 'feast_id': '5733', 'editors': ['438', '514']}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}}
        expected = {'feast_id': '5733', 'feast': 'https://cantus.org/feasts/5733/'}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    def test_resources_5(self):
        "Still works when no cross-reference results were found."
        record = {'id': '123', 'feast_id': '5733'}
        result = {'id': '123'}
        xrefs = {}
        expected = {}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    def test_resources_6(self):
        "Still works when there are many more cross-references than needed in the resource."
        record = {'id': '123', 'feast_id': '5733'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}, '444': {'display_name': 'D. Smith'},
            '555': {'display_name': 'F. Johnson'}}
        expected = {'feast_id': '5733', 'feast': 'https://cantus.org/feasts/5733/'}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    def test_resources_7(self):
        "Still works when there are no fields to cross-reference."
        record = {'id': '123'}
        result = {'id': '123'}
        xrefs = {'5733': {'name': 'Thanksgiving'}}
        expected = {}

        actual = Xref.resources(record, result, xrefs, self.handler.make_resource_url)

        assert actual == expected

    @testing.gen_test
    def test_issue_96(self):
        '''
        This is a regression test for GitHub issue 96.

        In this issue, cross-references to Notation resources were found to be incorrect. This test
        is to guarantee that look_up_xrefs() uses the "type" member of the LOOKUP object.
        '''
        results = {'123656': {'id': '123656', 'notation_style_id': '3895'},
                   'resources': {'123656': {'self': 'wee!'}},
                   'sort_order': []}
        self.solr = self.setUpSolr()
        self.solr.search_se.add('id:3895', {'id': '3895', 'name': 'German - neumatic'})
        expected = {'123656': {'id': '123656', 'notation_style': 'German - neumatic'},
                    'resources': {'123656': {'notation_style': 'https://cantus.org/notations/3895/',
                                             'notation_style_id': '3895', 'self': 'wee!'}},
                    'sort_order': [],
                   }

        actual = yield self.handler.look_up_xrefs(results, True)

        assert expected == actual


class TestLookupNameForResponse(shared.TestHandler):
    '''
    Tests for the ComplexHandler.look_up_xrefs().
    '''

    def setUp(self):
        "Make a ComplexHandler instance for testing."
        super(TestLookupNameForResponse, self).setUp()
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

        self.solr.search.assert_any_call('+type:feast +id:123', df='default_search')
        self.solr.search.assert_any_call('+type:source_status +id:456', df='default_search')
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

    @mock.patch('abbot.complex_handler.log.warn')
    @testing.gen_test
    def test_feast_lookup_fails(self, mock_warn):
        '''
        Both a feast_id and source_status_id to look up, but the feast lookup fails. The source
        status lookup should still succeed.
        '''
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {'source_status_desc': 'Ready'}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!
        def local_search_side_effect(query, **kwargs):
            '''
            This is a test-specific side effect for the util.search_solr() function.
            '''
            if '456' in query:
                return shared.make_future(shared.make_results([
                    {'id': '456', 'description': 'Ready'},
                ]))
            else:
                raise pysolrtornado.SolrError('test_feast_lookup_fails()')
        self.solr.search = mock.Mock(side_effect=local_search_side_effect)

        actual = yield self.handler.make_extra_fields(record, orig_record)

        assert expected == actual
        assert mock_warn.call_args[0][0].endswith('test_feast_lookup_fails()')

    @mock.patch('abbot.complex_handler.log.warn')
    @testing.gen_test
    def test_status_lookup_fails(self, mock_warn):
        '''
        Both a feast_id and source_status_id to look up, but the source status lookup fails. The
        feast lookup should still succeed.
        '''
        record = {}
        orig_record = {'feast_id': '123', 'source_status_id': '456'}
        expected = {'feast_desc': 'boiled goose and collard greens'}
        self.handler.returned_fields.append('feast_id')  # otherwise Source wouldn't usually do it!
        def local_search_side_effect(query, **kwargs):
            '''
            This is a test-specific side effect for the util.search_solr() function.
            '''
            if '123' in query:
                return shared.make_future(shared.make_results([
                    {'id': '123', 'description': 'boiled goose and collard greens'},
                ]))
            else:
                raise pysolrtornado.SolrError('test_feast_lookup_fails()')
        self.solr.search = mock.Mock(side_effect=local_search_side_effect)

        actual = yield self.handler.make_extra_fields(record, orig_record)

        assert expected == actual
        assert mock_warn.call_args[0][0].endswith('test_feast_lookup_fails()')


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
    def test_normal_behaviour_1(self, mock_basic, mock_xrefs, mock_extra):
        '''
        A request that goes normally.

        - self.hparams['include_resources'] is True
        # - output doesn't include "resources"
        # - self.look_up_xrefs() is called with every record
        # - self.make_extra_fields() is called with the output of look_up_xrefs()
        # - a returned resource is whatever make_extra_fields() returns
        '''
        self.handler.hparams['include_resources'] = True
        mock_basic.return_value = shared.make_future(
            ({'sort_order': ['1', '2', '3'], 'resources': 'res', '1': 'r1', '2': 'r2', '3': 'r3'}, 23))
        mock_xrefs.side_effect = lambda res, incl: shared.make_future(
            {'sort_order': ['1', '2', '3'], 'resources': 'res', '1': 'r1x', '2': 'r2x', '3': 'r3x'})
        # returns like 'r1xx'
        mock_extra.side_effect = lambda x, y: shared.make_future('{}x'.format(x))

        actual = yield self.handler.get_handler()

        assert actual[1] == 23
        assert actual[0] == {
            '1': 'r1xx',
            '2': 'r2xx',
            '3': 'r3xx',
            'resources': 'res',
            'sort_order': ['1', '2', '3'],
        }
        mock_basic.assert_called_once_with(resource_id=None, query=None)
        # mock_xrefs.assert_called_once_with((yield mock_basic.return_value)[0], True)
        assert mock_extra.call_count == 3
        mock_extra.assert_any_call('r1x', 'r1')
        mock_extra.assert_any_call('r2x', 'r2')
        mock_extra.assert_any_call('r3x', 'r3')

    @mock.patch('abbot.complex_handler.ComplexHandler.make_extra_fields')
    @mock.patch('abbot.complex_handler.ComplexHandler.look_up_xrefs')
    @mock.patch('abbot.complex_handler.ComplexHandler.basic_get')
    @testing.gen_test
    def test_normal_behaviour_2(self, mock_basic, mock_xrefs, mock_extra):
        '''
        Same as def test_normal_behaviour_1() BUT self.hparams['include_resources'] is False.
        '''
        self.handler.hparams['include_resources'] = False
        mock_basic.return_value = shared.make_future(
            ({'sort_order': ['1', '2', '3'], '1': 'r1', '2': 'r2', '3': 'r3'}, 23))
        mock_xrefs.side_effect = lambda res, incl: shared.make_future(
            {'sort_order': ['1', '2', '3'], '1': 'r1x', '2': 'r2x', '3': 'r3x'})
        mock_extra.side_effect = lambda x, y: shared.make_future('{}x'.format(x))

        actual = yield self.handler.get_handler()

        assert actual[0] == {
            '1': 'r1xx',
            '2': 'r2xx',
            '3': 'r3xx',
            'sort_order': ['1', '2', '3'],
        }
