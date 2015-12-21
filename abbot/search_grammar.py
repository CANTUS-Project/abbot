#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbot/search_grammar.py
# Purpose:                "Parsimonious" grammar for SEARCH queries.
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
"Parsimonious" grammar for SEARCH queries.

The grammar is held in a separate file, with a dedicated grammar-testing function, to ease testing.
'''

from parsimonious import exceptions, grammar

GRAMMAR_STRING = '''
    query = term+

    character = ~"[A-Za-z0-9]"
    space = ' '
    character_or_space = character / space

    text = character+
    quoted_text = '"' character_or_space* '"'

    default_field = quoted_text / text
    named_field = (text ':' quoted_text) / (text ':' text)

    term = (named_field / default_field) space*
'''

SEARCH_GRAMMAR = grammar.Grammar(GRAMMAR_STRING)


def it_parses(it, reraise=False):
    '''
    Determine whether "it" parses successfully with the SEARCH query grammar.

    :param str it: A query string to test.
    :param bool reraise: Whether to re-raise the exception given by Parsimonious. Defaults is ``False``.
    :returns: Whether the query string parses successfully.
    :rtype: bool

    .. note:: That this function makes no guarantee that the result is parsed as you expect---just
        that it was successfully parsed.
    '''
    try:
        result = SEARCH_GRAMMAR.parse(it)
        if reraise:
            print(str(result))
        return True
    except (exceptions.ParseError, exceptions.IncompleteParseError, exceptions.VisitationError) as exc:
        if reraise:
            raise exc
        return False
