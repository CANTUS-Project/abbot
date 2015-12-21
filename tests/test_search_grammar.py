#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_search_grammar.py
# Purpose:                Tests for the "Parsimonious" grammar for SEARCH queries.
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
Tests for the "Parsimonious" grammar for SEARCH queries.
'''

from abbot.search_grammar import it_parses


class TestWhetherItParses(object):
    "Simple tests using the it_parses() function."

    # single field --------------------
    # default field
    def test_single_1(self):
        assert it_parses('asdf')

    def test_single_2(self):
        assert it_parses('"asdf"')

    def test_single_3(self):
        assert it_parses('"as df"')

    # named field
    def test_single_4(self):
        assert it_parses('key:value')

    def test_single_5(self):
        assert it_parses('key:"value"')

    def test_single_6(self):
        assert it_parses('key:"val ue"')

    def test_single_7(self):
        assert not it_parses('"key":"value"')

    def test_single_8(self):
        assert not it_parses('"ke y":value')

    def test_single_9(self):
        assert not it_parses('key:"value')

    def test_single_10(self):
        assert not it_parses(':value"')

    def test_single_11(self):
        assert not it_parses(':value')

    def test_single_12(self):
        assert not it_parses('key:')

    # many fields ---------------------
    def test_many_1(self):
        assert it_parses('as df')

    def test_many_2(self):
        assert it_parses('one:two three:four')

    def test_many_3(self):
        assert it_parses('one:"tw o" three:"fo ur"')

    def test_many_4(self):
        assert it_parses('as two:five one:"four teen" df')

    def test_many_5(self):
        assert not it_parses('one: two:three')
