#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           holy_orders
# Program Description:    Update program for the Abbot Cantus API server.
#
# Filename:               holy_orders/test_configuration.py
# Purpose:                Tests for Holy Orders' "configuration" module.
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
Tests for Holy Orders' "configuration" module.
'''

# pylint: disable=protected-access
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

import configparser
import datetime
import os.path
import unittest
from unittest import mock

from hypothesis import assume, given, strategies as strats
import pytest

from holy_orders import configuration


class TestLoad(unittest.TestCase):
    '''
    Tests for load().
    '''

    @given(strats.text())
    def test_path_doesnt_exist(self, config_path):
        '''
        When the "config_path" doesn't exist, raise SystemExit.
        '''
        # don't test invalid EXT4 filenames
        assume(config_path != '.')
        assume(config_path != '..')
        assume('\0' not in config_path)
        with pytest.raises(RuntimeError) as err:
            configuration.load(config_path)
        assert err.value.args[0] == configuration._OPEN_INI_ERROR.format(config_path)

    def test_path_isnt_file(self):
        '''
        When the "config_path" exists, but it's a directory, raise SystemExit.
        '''
        config_path = '/usr'
        with pytest.raises(RuntimeError) as err:
            configuration.load(config_path)
        assert err.value.args[0] == configuration._OPEN_INI_ERROR.format(config_path)

    def test_file_isnt_ini(self):
        '''
        When the "config_path" exists and is a file, but not a valid INI file, raise SystemExit.
        '''
        config_path = os.path.join(os.path.split(__file__)[0], 'test_drupal_to_solr.py')
        with pytest.raises(configparser.Error) as err:
            configuration.load(config_path)
        assert config_path in err.value.args[0]

    def test_loads_correctly(self):
        '''
        When the "config_path" exists, is a directory, and is valid JSON, load it.
        '''
        config_path = os.path.join(os.path.split(__file__)[0], 'sample.ini')
        actual = configuration.load(config_path)
        assert actual['just']['basic'] == 'ini file'


class TestUpdateSaveConfig(unittest.TestCase):
    '''
    Test for update_save_config().
    '''

    @mock.patch('holy_orders.configuration.json')
    @mock.patch('holy_orders.configuration._now_wrapper')
    @given(strats.lists(strats.sampled_from(['a', 'b', 'c', 'd', 'e', 'genres', 'chants', 'feasts']),
                        unique=True, min_size=1),
           strats.lists(strats.sampled_from(['a', 'b', 'c', 'd', 'e', 'genres', 'chants', 'feasts']),
                        unique=True))
    def test_update_works(self, mock_now, mock_json, to_update, failed_types):
        '''
        That update_save_config() works as expected. This uses the "hypothesis" library to test all
        sorts of combinations of "to_update" and "failed_types".
        '''
        config = {'last_updated': {}}
        config_path = '/usr/local/whatever'
        # 1443803520.0  is  2015/09/02  16:32
        mock_now.return_value = datetime.datetime(2015, 10, 2, 16, 32, tzinfo=datetime.timezone.utc)
        timestamp = 1443803520.0
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        # setup mock on "json" module
        mock_json.dump = mock.Mock()

        with mock.patch('holy_orders.configuration.open', mock_open, create=True):
            configuration.update_save_config(to_update, failed_types, config, config_path)

        mock_open.assert_called_once_with(config_path, 'w')
        mock_json.dump.assert_called_once_with(
            config,
            mock_open.return_value,  # mock.ANY doesn't work here with CPython 3.5 ...
            indent='\t',
            sort_keys=True)
        # Ensure everything saved in the dict was in "to_update" and not "failed_types", and has
        # the proper timestamp.
        saved_conf = mock_json.dump.call_args[0][0]
        for key in saved_conf['last_updated']:
            assert key in to_update
            assert key not in failed_types
            assert timestamp == saved_conf['last_updated'][key]
