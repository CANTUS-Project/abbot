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
