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

    def test_default_field(self):
        assert it_parses('asdf')
        assert it_parses('"asdf"')
        assert it_parses('"as df"')

    def test_characters_with_accents(self):
        lowercase_vowels = [
            'á', 'à', 'ä', 'â',
            'é', 'è', 'ë', 'ê',
            'í', 'ì', 'ï', 'î',
            'ó', 'ò', 'ö','ô',
            'ú','ù','ü','û',
        ]
        for letter in lowercase_vowels:
            assert it_parses(letter)

        uppercase_vowels = [
            'Á', 'À', 'Ä', 'Â',
            'É', 'È', 'Ë', 'Ê',
            'Í', 'Ì', 'Ï', 'Î',
            'Ó', 'Ò', 'Ö', 'Ô',
            'Ú', 'Ù', 'Ü', 'Û',
        ]
        for letter in uppercase_vowels:
            assert it_parses(letter)

        others = ['ß', 'Ç', 'ç']
        for letter in others:
            assert it_parses(letter)

    def test_named_field(self):
        assert it_parses('key:value')
        assert it_parses('key:"value"')
        assert it_parses('key:"val ue"')
        assert it_parses('ke_ey:"val ue"')
        assert not it_parses('"key":"value"')
        assert not it_parses('"ke y":value')
        assert not it_parses('key:"value')
        assert not it_parses(':value"')
        assert not it_parses(':value')
        assert not it_parses('key:')

    def test_many_fields(self):
        assert it_parses('as df')
        assert it_parses('one:two three:four')
        assert it_parses('one:"tw o" three:"fo ur"')
        assert it_parses('as two:five one:"four teen" df')
        assert not it_parses('one: two:three')


class TestWildcardTokens(object):
    """
    Tests for the wildcard operators * and ?
    These are both often used in the same situations.
    """

    def test_star(self):
        assert it_parses('*')
        assert it_parses('field:*')
        assert it_parses('field:as*')
        assert it_parses('field:*df')
        assert it_parses('field:as*f')

    def test_double_star(self):
        assert not it_parses('**')
        assert not it_parses('field:**')
        assert not it_parses('field:as**')
        assert not it_parses('field:**df')
        assert not it_parses('field:as**f')

    def test_quoted_star(self):
        assert it_parses('"*"')
        assert it_parses('field:"*"')
        assert it_parses('field:"as*"')
        assert it_parses('field:"*df"')
        assert it_parses('field:"as*f"')

    def test_quoted_double_star(self):
        assert not it_parses('"**"')
        assert not it_parses('field:"**"')
        assert not it_parses('field:"as**"')
        assert not it_parses('field:"**df"')
        assert not it_parses('field:"as**f"')

    def test_qmark(self):
        assert it_parses('?')
        assert it_parses('field:?')
        assert it_parses('field:as?')
        assert it_parses('field:?df')
        assert it_parses('field:as?f')

    def test_double_qmark(self):
        "Double question mark should be fine; it means two wildcard characters."
        assert it_parses('??')
        assert it_parses('field:??')
        assert it_parses('field:as??')
        assert it_parses('field:??df')
        assert it_parses('field:as??f')

    def test_quoted_qmark(self):
        assert it_parses('"?"')
        assert it_parses('field:"?"')
        assert it_parses('field:"as?"')
        assert it_parses('field:"?df"')
        assert it_parses('field:"as?f"')

    def test_quoted_double_qmark(self):
        assert it_parses('"??"')
        assert it_parses('field:"??"')
        assert it_parses('field:"as??"')
        assert it_parses('field:"??df"')
        assert it_parses('field:"as??f"')


class TestBooleans(object):
    '''
    Tests for the boolean operators:
    - AND and &&
    - OR and ||
    - NOT and !
    - +
    - -
    '''

    def test_plus(self):
        assert it_parses('+type:genre')
        assert it_parses('type:"gen re" +blink:four')
        assert it_parses('+type:"gen re" +blink:four')
        assert it_parses('+fabulous')
        assert it_parses('once +fabulous')
        assert it_parses('+once +fabulous')

    def test_minus(self):
        assert it_parses('-type:genre')
        assert it_parses('type:"gen re" -blink:four')
        assert it_parses('-type:"gen re" -blink:four')
        assert it_parses('-fabulous')
        assert it_parses('once -fabulous')
        assert it_parses('-once -fabulous')

    def test_exclamation(self):
        assert it_parses('!type:genre')
        assert it_parses('type:"gen re" !blink:four')
        assert it_parses('!type:"gen re" !blink:four')
        assert it_parses('!fabulous')
        assert it_parses('once !fabulous')
        assert it_parses('!once !fabulous')

    def test_boolean_infix_1(self):
        "These are some usual things."
        operators = ('AND', 'OR', 'NOT', '&&', '||')
        for operator in operators:
            assert not it_parses('{} branch'.format(operator))
            assert not it_parses('{} tree:branch'.format(operator))
            assert not it_parses('{} once:"in a lifetime"'.format(operator))
            assert not it_parses('branch {}'.format(operator))
            assert not it_parses('tree:branch {}'.format(operator))
            assert not it_parses('once:"in a lifetime" {}'.format(operator))
            assert it_parses('branch {} tree'.format(operator))
            assert it_parses('branch:tree {} your:mom'.format(operator))
            assert it_parses('once:"in a lifetime" {} what:"a great opportunity"'.format(operator))
            assert it_parses('branch {} you:mom {} what:"in a lifetime"'.format(operator, operator))

    def test_boolean_infix_2(self):
        "These are some weird things."
        assert it_parses('type:appetizer AND NOT name:soup')
        assert it_parses('type:appetizer AND !name:soup')
        assert it_parses('type:appetizer && !name:soup')
        assert it_parses('type:appetizer &&  NOT  name:soup')
        assert not it_parses('type:appetizer ANDNOT name:soup')
        assert not it_parses('type:appetizer AND!name:soup')
        assert not it_parses('type:appetizer &&!name:soup')
        assert not it_parses('type:appetizer &&NOT  name:soup')
        assert not it_parses('type:appetizer &&& name:soup')
