#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/test_main.py
# Purpose:                Tests for __main__.py of the Abbott server.
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
Tests for ``__main__.py`` of the Abbott server.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

import unittest
from unittest import mock
from tornado import concurrent, httpclient, testing, web
import pysolrtornado
from abbott import __main__ as main


def make_future(with_this):
    '''
    Creates a new :class:`Future` with the function's argument as the result.
    '''
    val = concurrent.Future()
    val.set_result(with_this)
    return val


class TestAbbott(unittest.TestCase):
    '''
    Tests for module-level things.
    '''

    def get_solr_mock(self):
        '''
        Return a mock Solr object.
        '''
        post = mock.Mock(spec_set=pysolrtornado.Solr)
        # so the async search() method returns 'search results' when yielded
        post.search.return_value = make_future('search results')
        return post

    def test_singular_resource_to_plural_1(self):
        "When the singular form has a corresponding pural."
        self.assertEqual('cantusids', main.singular_resource_to_plural('cantusid'))

    def test_singular_resource_to_plural_2(self):
        "When the singular form doesn't have a corresponding plural."
        self.assertIsNone(main.singular_resource_to_plural('automobiles'))

    @mock.patch('abbott.__main__.SOLR')
    def test_ask_solr_by_id_1(self, mock_solr):
        "Basic test."
        mock_solr = self.get_solr_mock()
        expected = 'search results'
        actual = yield main.ask_solr_by_id('genre', '162')
        self.assertEqual(expected, actual)
        main.SOLR.search.assert_called_once_with('+type:genre +id:162')
