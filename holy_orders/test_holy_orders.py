#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           holy_orders
# Program Description:    Update program for the Abbot Cantus API server.
#
# Filename:               holy_orders/test_holy_orders.py
# Purpose:                Tests for Holy Orders.
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
Tests for Holy Orders.
'''

import datetime
import json
import os.path
import pathlib
import subprocess
import unittest
from unittest import mock

from tornado import httpclient

from hypothesis import assume, given, strategies as strats

import holy_orders.__main__ as holy_orders


class TestShouldUpdateThis(unittest.TestCase):
    '''
    Tests for should_update_this().
    '''

    def test_res_type_not_in_update_freq(self):
        '''
        When the resource type isn't in the "update_frequency" config member, raise KeyError.
        '''
        config = {'update_frequency': {'chant': 'never'}, 'last_updated': {'feast': 'Tuesday'}}
        resource_type = 'feast'
        self.assertRaises(KeyError, holy_orders.should_update_this, resource_type, config)

    def test_res_type_not_in_last_updated(self):
        '''
        When the resource type isn't in the "last_updated" config member, raise KeyError.
        '''
        config = {'update_frequency': {'chant': 'never'}, 'last_updated': {'feast': 'Tuesday'}}
        resource_type = 'chant'
        self.assertRaises(KeyError, holy_orders.should_update_this, resource_type, config)

    @mock.patch('holy_orders.__main__._now_wrapper')
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

        actual = holy_orders.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.__main__._now_wrapper')
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

        actual = holy_orders.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.__main__._now_wrapper')
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

        actual = holy_orders.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.__main__._now_wrapper')
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

        actual = holy_orders.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.__main__._now_wrapper')
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

        actual = holy_orders.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()

    @mock.patch('holy_orders.__main__._now_wrapper')
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

        actual = holy_orders.should_update_this(resource_type, config)

        self.assertEqual(expected, actual)
        mock_now.assert_called_once_with()


class TestConvertUpdate(unittest.TestCase):
    '''
    Tests for convert_update().
    '''

    @mock.patch('holy_orders.__main__.pathlib')
    @mock.patch('holy_orders.__main__.subprocess')
    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_everything_works(self, mock_now, mock_subp, mock_pathlib):
        '''
        convert_update() when everything goes according to plan.
        '''
        mock_now.return_value = datetime.datetime(2020, 1, 3, 4, 20, 45, 1024,
                                                  tzinfo=datetime.timezone.utc)
        temp_directory = '/tmp/hollabackgirls'
        conversion_script_path = '/usr/bin/inkscape'  # Inkscape opening: punishment for bad mocking
        update = '<xml quality="best"></xml>'
        drupal_xml_pathname = '{}/20200103042045001024.xml'.format(temp_directory)
        solr_xml_pathname = '{}/20200103042045001024-out.xml'.format(temp_directory)
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        mock_open.return_value.write.return_value = len(update)
        # setup mock on subprocess
        mock_subp.check_output = mock.Mock()
        # setup mock on pathlib
        mock_Path = mock.Mock()  # with the capital, this is the Path object returned
        mock_Path.exists = mock.Mock()
        mock_Path.exists.return_value = True
        mock_pathlib.Path = mock.Mock()
        mock_pathlib.Path.return_value = mock_Path
        expected = str(mock_Path)

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            actual = holy_orders.convert_update(temp_directory, conversion_script_path, update)

        self.assertEqual(expected, actual)
        mock_open.return_value.write.assert_called_once_with(update)
        mock_subp.check_output.assert_called_once_with([conversion_script_path, drupal_xml_pathname])
        mock_pathlib.Path.assert_called_once_with(solr_xml_pathname)
        mock_Path.exists.assert_called_once_with()

    @mock.patch('holy_orders.__main__.pathlib')
    @mock.patch('holy_orders.__main__.subprocess')
    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_drupal_output_fails(self, mock_now, mock_subp, mock_pathlib):
        '''
        convert_update() when writing Drupal XML to a file fails.
        '''
        mock_now.return_value = datetime.datetime(2020, 1, 3, 4, 20, 45, 1024,
                                                  tzinfo=datetime.timezone.utc)
        temp_directory = '/tmp/hollabackgirls'
        conversion_script_path = '/usr/bin/inkscape'  # Inkscape opening: punishment for bad mocking
        update = '<xml quality="best"></xml>'
        drupal_xml_pathname = '{}/20200103042045001024.xml'.format(temp_directory)
        solr_xml_pathname = '{}/20200103042045001024-out.xml'.format(temp_directory)
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        mock_open.return_value.write.return_value = 0  # NOTE: this causes the failure
        # setup mock on subprocess
        mock_subp.check_output = mock.Mock()
        # setup mock on pathlib
        mock_Path = mock.Mock()  # with the capital, this is the Path object returned
        mock_Path.exists = mock.Mock()
        mock_Path.exists.return_value = True
        mock_pathlib.Path = mock.Mock()
        mock_pathlib.Path.return_value = mock_Path

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            self.assertRaises(RuntimeError, holy_orders.convert_update, temp_directory, conversion_script_path, update)

        mock_open.return_value.write.assert_called_once_with(update)
        self.assertEqual(0, mock_subp.check_output.call_count)
        self.assertEqual(0, mock_pathlib.Path.call_count)
        self.assertEqual(0, mock_Path.exists.call_count)

    @mock.patch('holy_orders.__main__.pathlib')
    @mock.patch('holy_orders.__main__.subprocess')
    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_conversion_script_fails(self, mock_now, mock_subp, mock_pathlib):
        '''
        convert_update() when the conversion script fails
        '''
        mock_now.return_value = datetime.datetime(2020, 1, 3, 4, 20, 45, 1024,
                                                  tzinfo=datetime.timezone.utc)
        temp_directory = '/tmp/hollabackgirls'
        conversion_script_path = '/usr/bin/inkscape'  # Inkscape opening: punishment for bad mocking
        update = '<xml quality="best"></xml>'
        drupal_xml_pathname = '{}/20200103042045001024.xml'.format(temp_directory)
        solr_xml_pathname = '{}/20200103042045001024-out.xml'.format(temp_directory)
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        mock_open.return_value.write.return_value = len(update)
        # setup mock on subprocess
        mock_subp.check_output = mock.Mock()
        mock_subp.CalledProcessError = subprocess.CalledProcessError
        mock_subp.check_output.side_effect = mock_subp.CalledProcessError(1, 'python')  # NOTE: this causes the failure
        # setup mock on pathlib
        mock_Path = mock.Mock()  # with the capital, this is the Path object returned
        mock_Path.exists = mock.Mock()
        mock_Path.exists.return_value = True
        mock_pathlib.Path = mock.Mock()
        mock_pathlib.Path.return_value = mock_Path

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            self.assertRaises(RuntimeError, holy_orders.convert_update, temp_directory, conversion_script_path, update)

        mock_open.return_value.write.assert_called_once_with(update)
        mock_subp.check_output.assert_called_once_with([conversion_script_path, drupal_xml_pathname])
        self.assertEqual(0, mock_pathlib.Path.call_count)
        self.assertEqual(0, mock_Path.exists.call_count)

    @mock.patch('holy_orders.__main__.pathlib')
    @mock.patch('holy_orders.__main__.subprocess')
    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_missing_solrxml(self, mock_now, mock_subp, mock_pathlib):
        '''
        convert_update() when the Solr XML file isn't there.
        '''
        mock_now.return_value = datetime.datetime(2020, 1, 3, 4, 20, 45, 1024,
                                                  tzinfo=datetime.timezone.utc)
        temp_directory = '/tmp/hollabackgirls'
        conversion_script_path = '/usr/bin/inkscape'  # Inkscape opening: punishment for bad mocking
        update = '<xml quality="best"></xml>'
        drupal_xml_pathname = '{}/20200103042045001024.xml'.format(temp_directory)
        solr_xml_pathname = '{}/20200103042045001024-out.xml'.format(temp_directory)
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        mock_open.return_value.write.return_value = len(update)
        # setup mock on subprocess
        mock_subp.check_output = mock.Mock()
        # setup mock on pathlib
        mock_Path = mock.Mock()  # with the capital, this is the Path object returned
        mock_Path.exists = mock.Mock()
        mock_Path.exists.return_value = False  # NOTE: this causes the error
        mock_pathlib.Path = mock.Mock()
        mock_pathlib.Path.return_value = mock_Path

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            self.assertRaises(RuntimeError, holy_orders.convert_update, temp_directory, conversion_script_path, update)

        mock_open.return_value.write.assert_called_once_with(update)
        mock_subp.check_output.assert_called_once_with([conversion_script_path, drupal_xml_pathname])
        mock_pathlib.Path.assert_called_once_with(solr_xml_pathname)
        mock_Path.exists.assert_called_once_with()


class TestSubmitUpdate(unittest.TestCase):
    '''
    Tests for submit_update().
    '''

    @mock.patch('holy_orders.__main__.httpclient')
    def test_everything_works(self, mock_httpclient):
        '''
        submit_update() when everything goes according to plan, and the submission URL has a
        trailing slash.
        '''
        update_pathname = '123abc.xml'
        solr_url = 'http::/com.checkit/'
        exp_update_url = '{}update?commit=true'.format(solr_url)
        update_body = '<xml funlevel="woo"/>'
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        mock_open.return_value.read.return_value = update_body

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            holy_orders.submit_update(update_pathname, solr_url)

        mock_open.return_value.read.assert_called_once_with()
        mock_client.fetch.assert_called_once_with(exp_update_url, method='POST', body=update_body,
                                                  headers={'Content-Type': 'application/xml'})

    @mock.patch('holy_orders.__main__.httpclient')
    def test_Solr_is_borked(self, mock_httpclient):
        '''
        submit_update() when Solr doesn't like the update, and the submission URL does not end with
        a trailing slash.
        '''
        update_pathname = '123abc.xml'
        solr_url = 'http::/com.trailingslash'
        exp_update_url = '{}/update?commit=true'.format(solr_url)
        update_body = '<xml funlevel="woo"/>'
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()
        mock_client.fetch.side_effect = IOError('whatever, man')
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        mock_open.return_value.read.return_value = update_body

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            self.assertRaises(RuntimeError, holy_orders.submit_update, update_pathname, solr_url)

        mock_open.return_value.read.assert_called_once_with()
        mock_client.fetch.assert_called_once_with(exp_update_url, method='POST', body=update_body,
                                                  headers={'Content-Type': 'application/xml'})


class TestProcessAndSubmitUpdates(unittest.TestCase):
    '''
    Tests for process_and_submit_updates().
    '''

    @mock.patch('holy_orders.__main__.convert_update')
    @mock.patch('holy_orders.__main__.submit_update')
    @mock.patch('holy_orders.__main__.get_conversion_script_path')
    def test_everything_works(self, mock_get_path, mock_submit, mock_convert):
        '''
        everything works
        '''
        config = {'solr_url': 'http://solr.com'}
        updates = ['update one', 'update two', 'update three']
        mock_get_path.return_value = pathlib.Path('/usr/bin/gwenview')
        converted = ['converted one', 'converted two', 'converted three']
        mock_convert_returns = ['converted one', 'converted two', 'converted three']
        mock_convert.side_effect = lambda *args: mock_convert_returns.pop()
        expected = True

        actual = holy_orders.process_and_submit_updates(updates, config)

        self.assertEqual(expected, actual)
        mock_get_path.assert_called_once_with(config)
        self.assertEqual(len(updates), mock_convert.call_count)
        for i in range(len(updates)):
            mock_convert.assert_any_call(mock.ANY, str(mock_get_path.return_value), updates[i])
        self.assertEqual(len(converted), mock_submit.call_count)
        for i in range(len(converted)):
            mock_submit.assert_any_call(converted[i], config['solr_url'])

    @mock.patch('holy_orders.__main__.convert_update')
    @mock.patch('holy_orders.__main__.submit_update')
    @mock.patch('holy_orders.__main__.get_conversion_script_path')
    def test_conversion_fails(self, mock_get_path, mock_submit, mock_convert):
        '''
        everything else works when convert_update() fails with one
        '''
        config = {'solr_url': 'http://solr.com'}
        updates = ['update one', 'update two', 'update three']
        mock_get_path.return_value = pathlib.Path('/usr/bin/gwenview')
        converted = ['converted one', 'converted three']
        mock_convert_returns = ['converted one', RuntimeError('yuck'), 'converted three']
        def convert_mocker(*args):
            zell = mock_convert_returns.pop()
            if isinstance(zell, str):
                return zell
            else:
                raise zell
        mock_convert.side_effect = convert_mocker
        expected = False

        actual = holy_orders.process_and_submit_updates(updates, config)

        self.assertEqual(expected, actual)
        mock_get_path.assert_called_once_with(config)
        self.assertEqual(len(updates), mock_convert.call_count)
        for i in range(len(updates)):
            mock_convert.assert_any_call(mock.ANY, str(mock_get_path.return_value), updates[i])
        self.assertEqual(len(converted), mock_submit.call_count)
        for i in range(len(converted)):
            mock_submit.assert_any_call(converted[i], config['solr_url'])

    @mock.patch('holy_orders.__main__.convert_update')
    @mock.patch('holy_orders.__main__.submit_update')
    @mock.patch('holy_orders.__main__.get_conversion_script_path')
    def test_submission_fails(self, mock_get_path, mock_submit, mock_convert):
        '''
        submit_update() fails with one
        '''
        config = {'solr_url': 'http://solr.com'}
        updates = ['update one', 'update two', 'update three']
        mock_get_path.return_value = pathlib.Path('/usr/bin/gwenview')
        converted = ['converted one', 'converted two', 'converted three']
        mock_convert_returns = ['converted one', 'converted two', 'converted three']
        mock_convert.side_effect = lambda *args: mock_convert_returns.pop()
        mock_submit_returns = [None, RuntimeError('wow'), None]
        def submit_mocker(*args):
            zell = mock_submit_returns.pop()
            if zell:
                raise zell
        mock_submit.side_effect = submit_mocker
        expected = False

        actual = holy_orders.process_and_submit_updates(updates, config)

        self.assertEqual(expected, actual)
        mock_get_path.assert_called_once_with(config)
        self.assertEqual(len(updates), mock_convert.call_count)
        for i in range(len(updates)):
            mock_convert.assert_any_call(mock.ANY, str(mock_get_path.return_value), updates[i])
        self.assertEqual(len(converted), mock_submit.call_count)
        for i in range(len(converted)):
            mock_submit.assert_any_call(converted[i], config['solr_url'])


class TestGetConversionScriptPath(unittest.TestCase):
    '''
    Tests for get_conversion_script_path().
    '''

    def test_path_not_in_config(self):
        '''
        When there is no path in the configuration, raise SystemExit.
        '''
        config = {}
        self.assertRaises(SystemExit, holy_orders.get_conversion_script_path, config)

    def test_path_not_exists(self):
        '''
        When it's a relative path that doesn't exist, raise SystemExit.
        '''
        config = {'drupal_to_solr_script': '../../../../../../../../../../../../../../../sharks'}
        self.assertRaises(SystemExit, holy_orders.get_conversion_script_path, config)

    def test_path_is_directory(self):
        '''
        When the path is a directory, raise SystemExit.
        '''
        config = {'drupal_to_solr_scipr': '/usr'}
        self.assertRaises(SystemExit, holy_orders.get_conversion_script_path, config)

    def test_path_works(self):
        '''
        When the path is to a file, it's returned just fine.
        '''
        config = {'drupal_to_solr_script': '/usr/bin/python3'}
        actual = holy_orders.get_conversion_script_path(config)
        self.assertIsInstance(actual, pathlib.Path)


class TestLoadConfig(unittest.TestCase):
    '''
    Tests for load_config().
    '''

    @given(strats.text())
    def test_path_doesnt_exist(self, config_path):
        '''
        When the "config_path" doesn't exist, raise SystemExit.
        '''
        # don't test invalid EXT4 filenames
        assume('.' != config_path)
        assume('..' != config_path)
        assume('\0' not in config_path)
        self.assertRaises(SystemExit, holy_orders.load_config, config_path)

    def test_path_isnt_file(self):
        '''
        When the "config_path" exists, but it's a directory, raise SystemExit.
        '''
        config_path = '/usr'
        self.assertRaises(SystemExit, holy_orders.load_config, config_path)

    def test_file_isnt_json(self):
        '''
        When the "config_path" exists, and it's a file, but it's not valid JSON, raise SystemExit.
        '''
        config_path = '/usr/bin/env'
        self.assertRaises(SystemExit, holy_orders.load_config, config_path)

    def test_loads_correctly(self):
        '''
        When the "config_path" exists, is a directory, and is valid JSON, load it.
        '''
        config_path = os.path.join(os.path.split(__file__)[0], 'test.json')
        expected = {'a': 'b', 'c': 'd'}
        actual = holy_orders.load_config(config_path)
        self.assertEqual(expected, actual)


class TestUpdateSaveConfig(unittest.TestCase):
    '''
    Test for update_save_config().
    '''

    @mock.patch('holy_orders.__main__.json')
    @mock.patch('holy_orders.__main__._now_wrapper')
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

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            holy_orders.update_save_config(to_update, failed_types, config, config_path)

        mock_open.assert_called_once_with(config_path, 'w')
        mock_json.dump.assert_called_once_with(config, mock.ANY, indent='\t', sort_keys=True)
        # Ensure everything saved in the dict was in "to_update" and not "failed_types", and has
        # the proper timestamp.
        saved_conf = mock_json.dump.call_args[0][0]
        for key in saved_conf['last_updated']:
            self.assertTrue(key in to_update)
            self.assertFalse(key in failed_types)
            self.assertEqual(timestamp, saved_conf['last_updated'][key])


class TestMain(unittest.TestCase):
    '''
    Tests for main().
    '''

    @mock.patch('holy_orders.__main__.update_save_config')
    @mock.patch('holy_orders.__main__.process_and_submit_updates')
    @mock.patch('holy_orders.__main__.download_update')
    @mock.patch('holy_orders.__main__.should_update_this')
    def test_it_works(self, mock_should_update, mock_dl_update, mock_pasu, mock_usconf):
        '''
        When everything works (in that there are no exceptions).

        There are four resource types:
        - provenance, which doesn't need to be updated.
        - source, which fails during the call to download_update().
        - feast, which fails during the call to process_and_submit_updates().
        - chant, which works.
        '''
        config_path = os.path.join(os.path.split(__file__)[0], 'test_config.json')
        with open(config_path, 'r') as conf_p:
            config_file = json.load(conf_p)
        # everything but "provenance" needs to be updated
        mock_should_update.side_effect = lambda x, y: False if 'provenance' == x else True
        # the "source" Drupal URL is missing in the config
        mock_dl_update.side_effect = lambda x, y: ['downloaded {}'.format(x)] if 'chant' == x else []
        # "feast" fails in process_and_submit_updates()
        def pasu_side_effect(updates, config):
            if ['downloaded chant'] == updates:
                return True
            else:
                return False
        mock_pasu.side_effect = pasu_side_effect

        holy_orders.main(config_path)

        # should_update_this()
        self.assertEqual(4, mock_should_update.call_count)
        mock_should_update.assert_any_call('provenance', config_file)
        mock_should_update.assert_any_call('source', config_file)
        mock_should_update.assert_any_call('feast', config_file)
        mock_should_update.assert_any_call('chant', config_file)
        # download_update()
        mock_dl_update.assert_any_call('chant', config_file)
        mock_dl_update.assert_any_call('source', config_file)
        # process_and_submit_updates()
        mock_pasu.assert_called_once_with(['downloaded chant'], config_file)
        # update_save_config()
        mock_usconf.assert_called_once_with(['chant', 'feast', 'source'],
                                            ['feast', 'source'],
                                            config_file,
                                            config_path)


class TestUpdateDownloading(unittest.TestCase):
    '''
    Tests for download_update() and its helper funcitons download_chant_updates(),
    _collect_chant_ids(), and download_from_urls().
    '''

    def test_download_from_urls_1(self):
        '''
        With two URLs that return successfully.

        NOTE: this is an integration test that uses Tornado to make real Web requests.
        NOTE: if this test starts failing, first check whether it's because the responses from the
              URLs has changed.
        '''
        url_list = ['http://www.example.com/', 'http://www.example.org/']
        actual = holy_orders.download_from_urls(url_list)
        for body in actual:
            self.assertIsInstance(body, str)
            self.assertTrue(body.startswith('<!doctype html>'))

    def test_download_from_urls_2(self):
        '''
        When one of the URLs returns 404, the function returns an empty list.

        NOTE: this is an integration test that uses Tornado to make real Web requests.
        '''
        url_list = ['http://www.example.com/', 'http://www.example.org/pleasefourohfour/']
        actual = holy_orders.download_from_urls(url_list)
        self.assertEqual([], actual)

    def test_download_from_urls_3(self):
        '''
        When one of the URLs is invalid, the function returns an empty list.

        NOTE: this is an integration test that uses Tornado to make real Web requests.
        '''
        url_list = ['nkjhkjhlkjh3lkjhlk3jhlk3h3h3k2l']
        actual = holy_orders.download_from_urls(url_list)
        self.assertEqual([], actual)

    def test_download_from_urls_4(self):
        '''
        When one of the URLs is less invalid, the function returns an empty list.

        NOTE: this is an integration test that uses Tornado to make real Web requests.
        '''
        url_list = ['http://nkjhkjhlkjh3lkjhlk3jhlk3h3h3k2l']
        actual = holy_orders.download_from_urls(url_list)
        self.assertEqual([], actual)

    @given(strats.lists(strats.text('1234567890', min_size=1, max_size=10, average_size=6)))
    def test_collect_ids_1(self, list_of_ids):
        '''
        _collect_chant_ids() works with a single day of updates (str input).
        '''
        # build the XML document we'll input
        xml_docs = []
        for each_id in list_of_ids:
            xml_docs.append('<chant><id>{}</id></chant>'.format(each_id))
        xml_docs.insert(0, '<chants>')
        xml_docs.append('</chants>')
        xml_docs = ''.join(xml_docs)
        xml_docs = [xml_docs]

        # run the test and check results
        actual = holy_orders._collect_chant_ids(xml_docs)
        self.assertEqual(list_of_ids, actual)
        for each_id in actual:
            self.assertTrue(isinstance(each_id, str))

    @given(strats.lists(strats.text('1234567890', min_size=1, max_size=10, average_size=6)))
    def test_collect_ids_2(self, list_of_ids):
        '''
        _collect_chant_ids() works with a single day of updates (bytes input).
        '''
        # build the XML document we'll input
        xml_docs = []
        for each_id in list_of_ids:
            xml_docs.append('<chant><id>{}</id></chant>'.format(each_id))
        xml_docs.insert(0, '<chants>')
        xml_docs.append('</chants>')
        xml_docs = ''.join(xml_docs)
        xml_docs = bytes(xml_docs, 'UTF-8')
        xml_docs = [xml_docs]

        # run the test and check results
        actual = holy_orders._collect_chant_ids(xml_docs)
        self.assertEqual(list_of_ids, actual)
        for each_id in actual:
            self.assertTrue(isinstance(each_id, str))

    @given(strats.text())
    def test_collect_ids_3(self, garbage):
        '''
        _collect_chant_ids() doesn't crash when we give it invalid XML (str).
        '''
        expected = []
        actual = holy_orders._collect_chant_ids([garbage])
        self.assertEqual(expected, actual)

    @given(strats.binary())
    def test_collect_ids_4(self, garbage):
        '''
        _collect_chant_ids() doesn't crash when we give it invalid XML(bytes).
        '''
        expected = []
        actual = holy_orders._collect_chant_ids([garbage])
        self.assertEqual(expected, actual)

    def test_collect_ids_5(self):
        '''
        _collect_chant_ids() works with three days of updates (str input).
        '''
        # build the XML document we'll input
        xml_docs = []
        for i in range (3):
            xml_docs.append('''<chants>
            <chant><id>{}1</id></chant>
            <chant><id>{}2</id></chant>
            <chant><id>{}3</id></chant>
            </chants>
            '''.format(i, i, i))
        expected = ['01', '02', '03', '11', '12', '13', '21', '22', '23']
        print(str(xml_docs))

        # run the test and check results
        actual = holy_orders._collect_chant_ids(xml_docs)
        self.assertEqual(expected, actual)
        for each_id in actual:
            self.assertTrue(isinstance(each_id, str))

    @mock.patch('holy_orders.__main__.download_from_urls')
    @mock.patch('holy_orders.__main__.calculate_chant_updates')
    @mock.patch('holy_orders.__main__._collect_chant_ids')
    def test_download_chant_updates_1(self, mock_colids, mock_calcup, mock_download):
        '''
        Make sure it works.
        '''
        config = {'drupal_urls': {'drupal_url': 'a', 'chants_updated': '{drupal_url}/b/{date}',
                                  'chant_id': '{drupal_url}/c/{id}'}}
        mock_download.return_value = 'check it out'  # just needs to be identifiable
        # first call to download_from_urls(): date-specific URLs
        mock_calcup.return_value = ['2012', '2013', '2014']
        exp_download_first_call = ['a/b/2012', 'a/b/2013', 'a/b/2014']
        # second call to download_from_urls(): chant-specific URLs
        mock_colids.return_value = ['1', '2', '3']
        exp_download_second_call = ['a/c/1', 'a/c/2', 'a/c/3']

        actual = holy_orders.download_chant_updates(config)

        self.assertEqual(mock_download.return_value, actual)
        mock_calcup.assert_called_once_with(config)
        mock_colids.assert_called_once_with(mock_download.return_value)
        self.assertEqual(2, mock_download.call_count)
        mock_download.assert_any_call(exp_download_first_call)
        mock_download.assert_any_call(exp_download_second_call)

    @mock.patch('holy_orders.__main__.download_from_urls')
    @mock.patch('holy_orders.__main__.calculate_chant_updates')
    @mock.patch('holy_orders.__main__._collect_chant_ids')
    def test_download_chant_updates_2(self, mock_colids, mock_calcup, mock_download):
        '''
        download_chant_updates() returns empty list when given bad "chants_updated"
        '''
        config = {'drupal_urls': {'drupal_url': 'a', 'chants_updated': '{drupal_url}/b/{}',
                                  'chant_id': '{drupal_url}/c/{id}'}}
        expected = []

        actual = holy_orders.download_chant_updates(config)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mock_download.call_count)
        self.assertEqual(0, mock_calcup.call_count)

    @mock.patch('holy_orders.__main__.download_from_urls')
    @mock.patch('holy_orders.__main__.calculate_chant_updates')
    @mock.patch('holy_orders.__main__._collect_chant_ids')
    def test_download_chant_updates_3(self, mock_colids, mock_calcup, mock_download):
        '''
        download_chant_updates() returns empty list when given bad "chant_id"
        '''
        config = {'drupal_urls': {'drupal_url': 'a', 'chants_updated': '{drupal_url}/b/{date}',
                                  'chant_id': '{drupal_url}/c/{}'}}
        mock_download.return_value = 'check it out'  # just needs to be identifiable
        # only one call to download_from_urls(): date-specific URLs
        mock_calcup.return_value = ['2012', '2013', '2014']
        exp_download_first_call = ['a/b/2012', 'a/b/2013', 'a/b/2014']
        expected = []

        actual = holy_orders.download_chant_updates(config)

        self.assertEqual(expected, actual)
        mock_calcup.assert_called_once_with(config)
        mock_colids.assert_called_once_with(mock_download.return_value)
        mock_download.assert_called_once_with(exp_download_first_call)

    @mock.patch('holy_orders.__main__.download_chant_updates')
    @mock.patch('holy_orders.__main__.download_from_urls')
    def test_download_update_1(self, mock_urls, mock_chants):
        '''
        download_update() with 'chant'
        '''
        resource_type = 'chant'
        config = 'lolz'
        mock_chants.return_value = 42

        actual = holy_orders.download_update(resource_type, config)

        self.assertEqual(mock_chants.return_value, actual)
        mock_chants.assert_called_once_with(config)
        self.assertEqual(0, mock_urls.call_count)

    @mock.patch('holy_orders.__main__.download_chant_updates')
    @mock.patch('holy_orders.__main__.download_from_urls')
    def test_download_update_2(self, mock_urls, mock_chants):
        '''
        download_update() with 'feast'
        '''
        resource_type = 'feast'
        config = {'drupal_urls': {'drupal_url': 'a', 'feast': '{drupal_url}b'}}
        mock_urls.return_value = 42

        actual = holy_orders.download_update(resource_type, config)

        self.assertEqual(mock_urls.return_value, actual)
        mock_urls.assert_called_once_with(['ab'])
        self.assertEqual(0, mock_chants.call_count)

    @mock.patch('holy_orders.__main__.download_chant_updates')
    @mock.patch('holy_orders.__main__.download_from_urls')
    def test_download_update_3(self, mock_urls, mock_chants):
        '''
        download_update() when the URL can't be formed from the config
        '''
        resource_type = 'beast'
        config = {'drupal_urls': {'drupal_url': 'a', 'feast': '{drupal_url}b'}}
        expected = []

        actual = holy_orders.download_update(resource_type, config)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mock_chants.call_count)
        self.assertEqual(0, mock_urls.call_count)
