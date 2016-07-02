#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_main.py
# Purpose:                Tests for the __main__ module.
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
Tests for the __main__ module.
'''

# pylint: disable=protected-access
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

import logging
from unittest import mock

import pytest
from tornado.options import Error as OptionsError

from abbot import __main__ as main


class TestLoadOptions(object):
    '''
    Tests for _load_options().
    '''

    @mock.patch('abbot.__main__.options')
    def test_1(self, mock_options):
        '''
        When parse_command_line() raises an options.Error.
        '''
        mock_options.parse_command_line.side_effect = OptionsError
        with pytest.raises(SystemExit):
            main._load_options()

    @mock.patch('abbot.__main__.options')
    def test_2(self, mock_options):
        '''
        When parse_command_line() works and there is no config file.
        '''
        mock_options.options_file = ''
        main._load_options()
        mock_options.parse_command_line.assert_called_with(final=False)

    @mock.patch('abbot.__main__.options')
    def test_3a(self, mock_options):
        '''
        When parse_command_line() works but parse_config_file() raises an options.Error.
        '''
        mock_options.options_file = 'asdfasdf'
        mock_options.parse_config_file.side_effect = OptionsError

        with pytest.raises(SystemExit):
            main._load_options()

        mock_options.parse_command_line.assert_called_with(final=False)

    @mock.patch('abbot.__main__.options')
    def test_3b(self, mock_options):
        '''
        When parse_command_line() works but parse_config_file() raises a FileNotFoundError.
        '''
        mock_options.options_file = 'asdfasdf'
        mock_options.parse_config_file.side_effect = FileNotFoundError

        with pytest.raises(SystemExit):
            main._load_options()

        mock_options.parse_command_line.assert_called_with(final=False)

    @mock.patch('abbot.__main__.options')
    def test_4(self, mock_options):
        '''
        When parse_command_line() and parse_config_file() both work.
        '''
        mock_options.options_file = 'asdfasdf'
        main._load_options()
        mock_options.parse_command_line.assert_called_with(final=False)
        mock_options.parse_config_file.assert_called_with('asdfasdf', final=True)


class TestSetLogLevel(object):
    '''
    Tests for _set_log_level().
    '''

    @mock.patch('abbot.__main__.options')
    @mock.patch('abbot.__main__.log')
    def the_tester(self, levelstr, levelobj, mock_log, mock_options):
        '''
        Call this function with "levelstr," which is the string to set at "options.logging," and
        "levelobj," which is the object to expect being set.

        Example:

        >>> the_tester('DEbuG', logging.DEBUG)
        '''
        mock_options.logging = levelstr
        main._set_log_level()
        mock_log.access_log.setLevel.assert_called_with(levelobj)
        mock_log.app_log.setLevel.assert_called_with(levelobj)
        mock_log.gen_log.setLevel.assert_called_with(levelobj)

    def test_debug(self):
        self.the_tester('DEbuG', logging.DEBUG)  # pylint: disable=no-value-for-parameter

    def test_info(self):
        self.the_tester('infO', logging.INFO)  # pylint: disable=no-value-for-parameter

    def test_warn(self):
        self.the_tester('wArN', logging.WARN)  # pylint: disable=no-value-for-parameter

    def test_error(self):
        self.the_tester('ERRor', logging.ERROR)  # pylint: disable=no-value-for-parameter

    def test_whaaaa(self):
        self.the_tester('whaaaAAAAaaa?!?!?!!???!!', logging.WARN)  # pylint: disable=no-value-for-parameter


class TestSetAddresses(object):
    '''
    Tests for _set_addresses().
    '''

    @mock.patch('abbot.__main__.options')
    def test_1(self, mock_options):
        '''
        When "port" isn't an integer.
        '''
        mock_options.port = 'fourteen'
        with pytest.raises(SystemExit):
            main._set_addresses()

    @mock.patch('abbot.__main__.options')
    def test_2(self, mock_options):
        '''
        When "port" is less than 1024.
        '''
        mock_options.port = 22
        with pytest.raises(SystemExit):
            main._set_addresses()

    @mock.patch('abbot.__main__.options')
    def test_3(self, mock_options):
        '''
        When "port" is greater than 32768.
        '''
        mock_options.port = 400000000
        with pytest.raises(SystemExit):
            main._set_addresses()

    @mock.patch('abbot.__main__.options')
    def test_5(self, mock_options):
        '''
        When everything works (HTTP).
        '''
        mock_options.port = 4000
        mock_options.hostname = 'com.com'
        mock_options.certfile = ''
        mock_options.keyfile = ''
        mock_options.ciphers = ''
        main._set_addresses()
        assert mock_options.server_name == 'http://com.com:4000/'

    @mock.patch('abbot.__main__.options')
    def test_6(self, mock_options):
        '''
        When everything works (HTTPS).
        '''
        mock_options.port = 4000
        mock_options.hostname = 'com.com'
        mock_options.certfile = 'dd'
        mock_options.keyfile = 'ee'
        mock_options.ciphers = 'ff'
        main._set_addresses()
        assert mock_options.server_name == 'https://com.com:4000/'
