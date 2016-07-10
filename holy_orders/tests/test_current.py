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
import sqlite3
import unittest
from unittest import mock

import iso8601
import pytest

from holy_orders import current


@pytest.fixture
def updates_db(request):
    '''
    Make an empty SQLite database in memory for use when testing the "updates DB."
    '''
    conn = sqlite3.connect(':memory:')
    conn.cursor().execute('CREATE TABLE rtypes (id INTEGER PRIMARY KEY, name TEXT, updated TEXT);')
    conn.commit()
    def finalizer():
        conn.close()
    request.addfinalizer(finalizer)
    return conn


def test_get_last_updated_1(updates_db):
    '''
    get_last_updated() when the most recent update was "never"
    '''
    updates_db.cursor().execute(
        'INSERT INTO rtypes (id, name, updated) VALUES (0, "feast", "never");')
    actual = current.get_last_updated(updates_db, 'feast')
    assert actual.year == 1969


def test_get_last_updated_2(updates_db):
    '''
    get_last_updated() when the most recent update was a real time
    '''
    updates_db.cursor().execute(
        'INSERT INTO rtypes (id, name, updated) VALUES (0, "feast", "2015-09-04T14:32:56-0000");')
    expected = datetime.datetime(2015, 9, 4, 14, 32, 56, tzinfo=datetime.timezone(datetime.timedelta(0)))
    actual = current.get_last_updated(updates_db, 'feast')
    assert expected == actual


class TestShouldUpdate(object):
    '''
    Tests for should_update().
    '''

    def test_should_update_1(self, updates_db):
        '''
        When the last update was "never," return True.
        '''
        rtype = 'chant'
        config = {'update_frequency': {'chant': '4h'}}
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "never");')
        assert current.should_update(rtype, config, updates_db) is True

    @mock.patch('holy_orders.current._now_wrapper')
    def test_should_update_2(self, mock_now, updates_db):
        '''
        When the last update was 4 days ago and the update frequency is 2 days, return True.
        '''
        rtype = 'chant'
        config = {'update_frequency': {'chant': '2d'}}
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "2015-09-04T00:00:00-0000");')
        mock_now.return_value = iso8601.parse_date('2015-09-08T00:00:00-0000')

        assert current.should_update(rtype, config, updates_db) is True

    @mock.patch('holy_orders.current._now_wrapper')
    def test_should_update_3(self, mock_now, updates_db):
        '''
        When the last update was 2 hours ago and the update frequency is 4 hours, return False.
        '''
        rtype = 'chant'
        config = {'update_frequency': {'chant': '4h'}}
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "2015-09-08T12:05:00-0000");')
        mock_now.return_value = iso8601.parse_date('2015-09-08T14:05:00-0000')

        assert current.should_update(rtype, config, updates_db) is False

    @mock.patch('holy_orders.current._now_wrapper')
    def test_should_update_4(self, mock_now, updates_db):
        '''
        When the last update was 3 hours ago and the update frequency is 3 hours, return True.
        '''
        rtype = 'chant'
        config = {'update_frequency': {'chant': '3h'}}
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "2015-09-08T11:05:00-0000");')
        mock_now.return_value = iso8601.parse_date('2015-09-08T14:05:00-0000')

        assert current.should_update(rtype, config, updates_db) is True

    @mock.patch('holy_orders.current._now_wrapper')
    def test_should_update_5(self, mock_now, updates_db):
        '''
        When the last update is 2 days in the future, return False.
        '''
        rtype = 'chant'
        config = {'update_frequency': {'chant': '3h'}}
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "2015-09-10T14:05:00-0000");')
        mock_now.return_value = iso8601.parse_date('2015-09-08T14:05:00-0000')

        assert current.should_update(rtype, config, updates_db) is False


class TestCalculateChantUpdates(object):
    '''
    Tests for calculate_chant_updates().
    '''

    @mock.patch('holy_orders.current._now_wrapper')
    def test_calc_chant_up_(self, mock_now, updates_db):
        '''
        Most recent update is in the future. Return empty list.
        '''
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "2015-09-11T14:05:00-0000");')
        mock_now.return_value = iso8601.parse_date('2015-09-10T14:05:00-0000')
        assert current.calculate_chant_updates(updates_db) == []

    @mock.patch('holy_orders.current._now_wrapper')
    def test_calc_chant_up_(self, mock_now, updates_db):
        '''
        Most recent update was earlier today. Return today and yesterday.
        '''
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "2015-09-10T12:05:00-0000");')
        mock_now.return_value = iso8601.parse_date('2015-09-10T14:05:00-0000')
        expected = [
            '20150910',
            '20150909',
        ]
        assert current.calculate_chant_updates(updates_db) == expected

    @mock.patch('holy_orders.current._now_wrapper')
    def test_calc_chant_up_(self, mock_now, updates_db):
        '''
        Most recent update was five days ago. Return today up to six days ago.
        '''
        updates_db.cursor().execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (0, "chant", "2015-09-05T14:04:00-0000");')
        mock_now.return_value = iso8601.parse_date('2015-09-10T14:05:00-0000')
        expected = [
            '20150910',
            '20150909',
            '20150908',
            '20150907',
            '20150906',
            '20150905',
            '20150904',
        ]
        assert current.calculate_chant_updates(updates_db) == expected
