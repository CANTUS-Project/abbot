#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_fixtures.py
# Purpose:                Tests for the test suite and its fixtures.
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
Tests for the test suite and its fixtures.
'''

from tornado import testing
import pytest

from abbot import util
import shared


class TestTestHandler(shared.TestHandler):
    '''
    Ensure that :class:`shared.TestHandler` is properly mocking Solr.

    By default, :class:`TestHandler` should install a simple mock that blocks requests from hitting
    ``pysolr-tornado`` in the :mod:`util` module.

    :class:`TestHandler optionally configures a complicated mock on the ``pysolr-tornado`` object
    that allows setting dynamic return values and suchlike.
    '''

    @testing.gen_test
    def test_default_mock(self):
        with pytest.raises(AssertionError):
            yield util.ask_solr_by_id('chant', '123')
        with pytest.raises(AssertionError):
            yield util.SOLR.search(123)
        with pytest.raises(AssertionError):
            yield util.SOLR.add(123)
        with pytest.raises(AssertionError):
            yield util.SOLR.delete(123)
        with pytest.raises(AssertionError):
            yield util.SOLR.more_like_this(123)
        with pytest.raises(AssertionError):
            yield util.SOLR.suggest_terms(123)
        with pytest.raises(AssertionError):
            yield util.SOLR.commit(123)
        with pytest.raises(AssertionError):
            yield util.SOLR.optimize(123)
        with pytest.raises(AssertionError):
            yield util.SOLR.extract(123)

    @testing.gen_test
    def test_featureful_mock(self):
        solr = self.setUpSolr()
        solr.search_se.add('1', {'1': '1'})
        actual = yield util.ask_solr_by_id('chant', '1')
        assert [{'1': '1'}] == actual.docs
        #
        actual = yield util.ask_solr_by_id('chant', '4')
        assert 0 == actual.hits


class TestSolrSideEffect(shared.TestHandler):
    '''
    Tests for :class:`shared.SolrMethodSideEffect`.

    The tests are the three examples shown in the docstring for that class.
    '''

    @testing.gen_test
    def test_example_1(self):
        se = shared.SolrMethodSideEffect()
        se.add('id:1', {'id': '1'})
        se.add('id:2', {'id': '2'})
        assert [{'id': '1'}] == (yield se('id:1')).docs
        assert [{'id': '2'}] == (yield se('id:2')).docs
        assert [{'id': '1'}] == (yield se('type:chant AND id:1')).docs
        assert [] == (yield se('type:chant AND id:3')).docs
        # for the following, the order can change arbitrarily because of dict iteration
        expected = [{'id': '1'}, {'id': '2'}]
        actual = (yield se('id:1 OR id:2')).docs
        assert expected[0] in actual
        assert expected[1] in actual

    @testing.gen_test
    def test_example_2(self):
        se = shared.SolrMethodSideEffect()
        se.add('*', {'id': '1'})
        se.add('*', {'id': '2'})
        # the order here should be the same as the order they were added in
        assert [{'id': '1'}, {'id': '2'}] == (yield se('*')).docs

    def test_counter_example_1(self):
        se = shared.SolrMethodSideEffect()
        with pytest.raises(TypeError):
            se.add(4, {'id': '4'})
        with pytest.raises(TypeError):
            se.add('id:4', 'broccoli')

    @testing.gen_test
    def test_counter_example_2(self):
        se = shared.SolrMethodSideEffect()
        se.add('1', {'id': '1'})
        assert [{'id': '1'}] == (yield se('1')).docs
        with pytest.raises(RuntimeError):
            se.add('2', {'id': '2'})


class TestSolrMock(shared.TestHandler):
    '''
    Tests for :class:`shared.SolrMock`.
    '''

    @testing.gen_test
    def test_search(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.search_se.add(key, expected)
        assert [expected] == (yield smock.search(key)).docs
        smock.search.assert_called_once_with(key)

    @testing.gen_test
    def test_add(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.add_se.add(key, expected)
        assert [expected] == (yield smock.add(key)).docs
        smock.add.assert_called_once_with(key)

    @testing.gen_test
    def test_delete(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.delete_se.add(key, expected)
        assert [expected] == (yield smock.delete(key)).docs
        smock.delete.assert_called_once_with(key)

    @testing.gen_test
    def test_more_like_this(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.more_like_this_se.add(key, expected)
        assert [expected] == (yield smock.more_like_this(key)).docs
        smock.more_like_this.assert_called_once_with(key)

    @testing.gen_test
    def test_suggest_terms(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.suggest_terms_se.add(key, expected)
        assert [expected] == (yield smock.suggest_terms(key)).docs
        smock.suggest_terms.assert_called_once_with(key)

    @testing.gen_test
    def test_commit(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.commit_se.add(key, expected)
        assert [expected] == (yield smock.commit(key)).docs
        smock.commit.assert_called_once_with(key)

    @testing.gen_test
    def test_optimize(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.optimize_se.add(key, expected)
        assert [expected] == (yield smock.optimize(key)).docs
        smock.optimize.assert_called_once_with(key)

    @testing.gen_test
    def test_extract(self):
        smock = shared.SolrMock()
        expected = {'a': 'a'}
        key = 'a'
        smock.extract_se.add(key, expected)
        assert [expected] == (yield smock.extract(key)).docs
        smock.extract.assert_called_once_with(key)
