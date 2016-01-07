#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_search_grammar.py
# Purpose:                Tests for the "Parsimonious" grammar for SEARCH queries.
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
        assert not it_parses('key:value:again')
        assert not it_parses('key:"value":again')

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


class TestParentheses(object):
    '''
    Tests for term grouping with parentheses.
    '''

    def test_single_parens_valid(self):
        "When there's only one ( and one ) in a valid query."
        assert it_parses('(forcefield)')
        assert it_parses('(force field)')
        assert it_parses('(force OR field)')
        assert it_parses('force AND (field OR broccoli)')
        assert it_parses('(force AND field) OR cheese')
        assert it_parses('(force && field) || (ginger && bread) NOT baking')
        assert it_parses('("force field")')
        assert it_parses('once:force AND ("fi eld" OR broccoli)')
        assert it_parses('(once:force AND field) OR variety:cheese')
        assert it_parses('(force && place:field) || (flavour:"ginger" && basis:"bread") NOT activity:baking')
        assert it_parses('type:(chant OR feast)')
        assert it_parses('left:"right" AND well_spring:("front and centre" OR groundswell)')
        # I don't know why somebody would do this, and it will return no results, but Solr accepts
        # it so we might as well accept it too!
        assert it_parses('+type:(name:feast OR name:chant)')

    def test_single_parens_invalid(self):
        "When there's only one ( and one ) in an invalid query."
        # NOTE: these look similar to the valid queries, but they are not the same!
        assert not it_parses('(force field')
        assert not it_parses('force field)')
        assert not it_parses('(force NOT field')
        assert not it_parses('force AND (field OR broccoli')
        assert not it_parses(')forcce field(')
        assert not it_parses('(')
        assert not it_parses(')')
        assert not it_parses('()')
        assert not it_parses('(    )')
        assert not it_parses('( ) force OR field')
        assert not it_parses('force NOT (  ) field')

    def test_many_parens_valid(self):
        "When there are many ( and ) in a valid query."
        assert it_parses('(force) (field)')
        assert it_parses('(force) AND (field)')
        assert it_parses('(force OR field) AND ("long onions" OR "green onions")')
        assert it_parses('title:("desperate macaroni" OR *macaroni) OR (category:"silly food")')
        assert it_parses('((one OR field:two) AND (two OR field:one)) NOT body:hatchback')
        assert it_parses('((one OR field:two) AND (two OR field:one) AND twist:asdf) NOT body:hatchback')
        assert it_parses('(((((a OR b) OR c) OR d) OR d) OR e) AND "lots of parentheses there"')
        # assert it_parses('')
        # assert it_parses('')
        # assert it_parses('')
        # assert it_parses('')
        # assert it_parses('')
        # assert it_parses('')

    def test_many_parens_invalid(self):
        "When there are many ( and ) in an invalid query."
        # NOTE: these look similar to the valid queries, but they are not the same!
        assert not it_parses('(force (field)')
        assert not it_parses('((')
        assert not it_parses('())()(()(()())())))(')
        assert not it_parses('(laser AND (beams OR tractor:beams) NOT (field:one field:two)')
        assert not it_parses('when (in OR place:"Rome"))')
        assert not it_parses(')))')
        assert not it_parses(')())')
        assert not it_parses(') b ( f ) g ) e')
        # assert not it_parses('')
        # assert not it_parses('')
        # assert not it_parses('')
        # assert not it_parses('')
        # assert not it_parses('')
        # assert not it_parses('')
        # assert not it_parses('')
