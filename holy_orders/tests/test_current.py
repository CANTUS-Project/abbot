#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           holy_orders
# Program Description:    Update program for the Abbot Cantus API server.
#
# Filename:               holy_orders/test_current.py
# Purpose:                Tests for the HolyOrders "current" module.
#
# Copyright (C) 2016 Christopher Antila
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
Tests for the HolyOrders "current" module.
'''

# pylint: disable=protected-access
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

import datetime
import unittest
from unittest import mock

from holy_orders import current


class TestShouldUpdateThis(unittest.TestCase):
    '''
    Tests for should_update_this().
    '''

    def test_should_update_1(self):
        '''
        When the resource type isn't in the "update_frequency" config member, raise KeyError.
        '''
        config = {'update_frequency': {'chant': 'never'}, 'last_updated': {'feast': 'Tuesday'}}
        resource_type = 'feast'
        self.assertRaises(KeyError, current.should_update_this, resource_type, config)

    def test_should_update_2(self):
        '''
        When the resource type isn't in the "last_updated" config member, raise KeyError.
        '''
        config = {'update_frequency': {'chant': 'never'}, 'last_updated': {'feast': 'Tuesday'}}
        resource_type = 'chant'
        self.assertRaises(KeyError, current.should_update_this, resource_type, config)

    @mock.patch('holy_orders.current._now_wrapper')
    def test_d_freq_too_soon(self, mock_now):
        '''
        When the update frequency is in days, and it's too soon to update.

        NB: we have to mock the now() function for else the tests would be different every time!
        '''
        # last_updated is 2015-09-07 00:00:00.0000
        config = {'update_frequency': {'chant': '4d'}, 'last_updated': {'chant': '1441584000.0'}}
        resource_type = 'chant'
        mock_now.return_value = datetime.datetime(2015, 9, 8, tzinfo=datetime.timezone.utc)
        expected = False

        actual = current.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.current._now_wrapper')
    def test_d_freq_equal(self, mock_now):
        '''
        When the update frequency is in days, and the update frequency is equal to the delta.

        NB: we have to mock the now() function for else the tests would be different every time!
        '''
        # last_updated is 2015-09-07 00:00:00.0000
        config = {'update_frequency': {'chant': '4d'}, 'last_updated': {'chant': '1441584000.0'}}
        resource_type = 'chant'
        mock_now.return_value = datetime.datetime(2015, 9, 11, tzinfo=datetime.timezone.utc)
        expected = True

        actual = current.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.current._now_wrapper')
    def test_d_freq_update(self, mock_now):
        '''
        When the update frequency is in days, and it's been longer than that many.

        NB: we have to mock the now() function for else the tests would be different every time!
        '''
        # last_updated is 2015-09-07 00:00:00.0000
        config = {'update_frequency': {'chant': '4d'}, 'last_updated': {'chant': '1441584000.0'}}
        resource_type = 'chant'
        mock_now.return_value = datetime.datetime(2015, 9, 14, tzinfo=datetime.timezone.utc)
        expected = True

        actual = current.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.current._now_wrapper')
    def test_h_freq_too_soon(self, mock_now):
        '''
        When the update frequency is in hours, and it's too soon to update.

        NB: we have to mock the now() function for else the tests would be different every time!
        '''
        # last_updated is 2015-09-07 00:00:00.0000
        config = {'update_frequency': {'chant': '4h'}, 'last_updated': {'chant': '1441584000.0'}}
        resource_type = 'chant'
        mock_now.return_value = datetime.datetime(2015, 9, 7, hour=1, tzinfo=datetime.timezone.utc)
        expected = False

        actual = current.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.current._now_wrapper')
    def test_h_freq_equal(self, mock_now):
        '''
        When the update frequency is in hours, and the update frequency is equal to the delta.

        NB: we have to mock the now() function for else the tests would be different every time!
        '''
        # last_updated is 2015-09-07 00:00:00.0000
        config = {'update_frequency': {'chant': '4h'}, 'last_updated': {'chant': '1441584000.0'}}
        resource_type = 'chant'
        mock_now.return_value = datetime.datetime(2015, 9, 8, hour=4, tzinfo=datetime.timezone.utc)
        expected = True

        actual = current.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.current._now_wrapper')
    def test_h_freq_update(self, mock_now):
        '''
        When the update frequency is in hours, and it's been longer than that many.

        NB: we have to mock the now() function for else the tests would be different every time!
        '''
        # last_updated is 2015-09-07 00:00:00.0000
        config = {'update_frequency': {'chant': '4h'}, 'last_updated': {'chant': '1441584000.0'}}
        resource_type = 'chant'
        mock_now.return_value = datetime.datetime(2015, 9, 8, hour=7, tzinfo=datetime.timezone.utc)
        expected = True

        actual = current.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()
