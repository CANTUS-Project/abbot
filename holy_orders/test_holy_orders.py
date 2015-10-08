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
import subprocess
import pathlib
import unittest
from unittest import mock

from tornado import httpclient

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


class TestDownloadUpdate(unittest.TestCase):
    '''
    Tests for download_update() and calculate_chant_updates().
    '''

    # this is weird, but I promise it's a mock of tornado.httpclient
    @mock.patch('holy_orders.__main__.httpclient')
    def test_down_works(self, mock_httpclient):
        '''
        When the Drupal server responds with 200 OK and all is well.
        '''
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()
        mock_response = mock.Mock()
        mock_response.body = 'response body'
        mock_client.fetch.return_value = mock_response
        # other setup
        resource_type = 'genre'
        config = {'drupal_urls': {'drupal_url': 'a', 'genre': '{drupal_url}b'}}
        expected = [mock_response.body]

        actual = holy_orders.download_update(resource_type, config)

        self.assertEqual(expected, actual)
        mock_client.fetch.assert_called_once_with('ab')
        mock_client.close.assert_called_once_with()

    @mock.patch('holy_orders.__main__.calculate_chant_updates')
    @mock.patch('holy_orders.__main__.httpclient')
    def test_down_works_with_chants(self, mock_httpclient, mock_ccu):
        '''
        When everything goes as planned, and the script is trying to update chants!
        '''
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()
        mock_response = mock.Mock()
        mock_response.body = 'response body'
        mock_client.fetch.return_value = mock_response
        # other setup
        resource_type = 'chant'
        config = {'drupal_urls': {'drupal_url': 'a', 'chant': '{drupal_url}b'}}
        expected = [mock_response.body, mock_response.body]
        mock_ccu.return_value = ['20150908', '20150909']

        actual = holy_orders.download_update(resource_type, config)

        self.assertEqual(expected, actual)
        self.assertEqual(2, mock_client.fetch.call_count)
        mock_client.fetch.assert_any_call('ab/20150908')
        mock_client.fetch.assert_any_call('ab/20150909')
        mock_client.close.assert_called_once_with()

    @mock.patch('holy_orders.__main__._log')
    @mock.patch('holy_orders.__main__.httpclient')
    def test_down_does_not_work(self, mock_httpclient, mock_log):
        '''
        When the Drupal server responds with a 500 and all is not well.
        '''
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()
        mock_client.fetch.side_effect = httpclient.HTTPError(500, 'Surfer Error')
        # other setup
        mock_log.warning = mock.Mock()
        resource_type = 'genre'
        config = {'drupal_urls': {'drupal_url': 'a', 'genre': '{drupal_url}b'}}
        expected = ['']

        actual = holy_orders.download_update(resource_type, config)

        self.assertEqual(expected, actual)
        mock_client.fetch.assert_called_once_with('ab')
        mock_client.close.assert_called_once_with()
        mock_log.warning.assert_called_once_with('Failed to download update for genre (HTTP 500: Surfer Error)')

    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_calc_future(self, mock_now):
        '''
        calculate_chant_updates(): last update is in the future
        '''
        mock_now.return_value = datetime.datetime(2015, 9, 10, 16, 32, tzinfo=datetime.timezone.utc)
        # 1441989120.0  is  2015/09/11  16:32
        config = {'last_updated': {'chant': '1441989120.0'}}
        expected = []
        actual = holy_orders.calculate_chant_updates(config)
        self.assertCountEqual(expected, actual)

    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_calc_same_day(self, mock_now):
        '''
        calculate_chant_updates():  last update was today (ask for yesterday and today)
        '''
        mock_now.return_value = datetime.datetime(2015, 9, 10, 16, 32, tzinfo=datetime.timezone.utc)
        # 1441894200.0  is  2015/09/10  14:10
        config = {'last_updated': {'chant': '1441894200.0'}}
        expected = ['20150909', '20150910']
        actual = holy_orders.calculate_chant_updates(config)
        self.assertCountEqual(expected, actual)

    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_calc_yesterday(self, mock_now):
        '''
        calculate_chant_updates():  last update was yesterday (ask for ante-yesterday, yesterday, and today)
        '''
        mock_now.return_value = datetime.datetime(2015, 9, 10, 16, 32, tzinfo=datetime.timezone.utc)
        # 1441816320.0  is  2015/09/09  16:32
        config = {'last_updated': {'chant': '1441816320.0'}}
        expected = ['20150908', '20150909', '20150910']
        actual = holy_orders.calculate_chant_updates(config)
        self.assertCountEqual(expected, actual)

    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_calc_five_days_ago(self, mock_now):
        '''
        calculate_chant_updates():  last update was five days ago (ask for today and up to six days ago)

        This test also ensures the function can deal with "backup up" over a month (i.e., that we
        won't try asking for September -2nd).
        '''
        # NOTE: the mock returns a different value than the other tests!
        mock_now.return_value = datetime.datetime(2020, 1, 3, 4, 20, tzinfo=datetime.timezone.utc)
        # 1577536440.0  is  2019/12/28  12:34
        config = {'last_updated': {'chant': '1577536440.0'}}
        expected = ['20200103', '20200102', '20200101', '20191231', '20191230', '20191229', '20191228']
        actual = holy_orders.calculate_chant_updates(config)
        self.assertCountEqual(expected, actual)


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

    def test_path_doesnt_exist(self):
        '''
        When the "config_path" doesn't exist, raise SystemExit.
        '''
        config_path = '/this/does/not/work'
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
        config_path = 'test.json'
        expected = {'a': 'b', 'c': 'd'}
        actual = holy_orders.load_config(config_path)
        self.assertEqual(expected, actual)


class TestUpdateSaveConfig(unittest.TestCase):
    '''
    Test for update_save_config().
    '''

    @mock.patch('holy_orders.__main__.json')
    @mock.patch('holy_orders.__main__._now_wrapper')
    def test_update_works(self, mock_now, mock_json):
        '''
        That update_save_config() works as expected. There will be one resource type that wasn't
        supposed to be updated, one that should have been updated but wasn't, and one that was
        updated as intended.
        '''
        config = {'last_updated': {'chant': '1441584000.0', 'source': '1441584000.0',
                                   'provenance': '1441584000.0'}}
        config_path = 'whatever_file.json'
        to_update = ['chant', 'source']
        failed_types = ['source']
        # 1443803520.0  is  2015/09/02  16:32
        mock_now.return_value = datetime.datetime(2015, 10, 2, 16, 32, tzinfo=datetime.timezone.utc)
        expected = {'last_updated': {'chant': '1443803520.0', 'source': '1441584000.0',
                                     'provenance': '1441584000.0'}}
        # setup mock on open() as a context manager
        mock_open = mock.mock_open()
        # setup mock on "json" module
        mock_json.dump = mock.Mock()

        with mock.patch('holy_orders.__main__.open', mock_open, create=True):
            holy_orders.update_save_config(to_update, failed_types, config, config_path)

        mock_open.assert_called_once_with(config_path, 'w')
        mock_json.dump.assert_called_once_with(config, mock.ANY, indent='\t', sort_keys=True)


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
        '''
        config_path = 'test_config.json'
        with open(config_path, 'r') as conf_p:
            config_file = json.load(conf_p)
        # pretend only "chant" and "source" need updating (not "provenance")
        mock_should_update.side_effect = lambda x, y: False if 'provenance' == x else True
        # the "source" Drupal URL is missing in the config
        mock_dl_update.side_effect = lambda x, y: ['downloaded {}'.format(x)] if 'chant' == x else []

        holy_orders.main(config_path)

        # should_update_this()
        self.assertEqual(3, mock_should_update.call_count)
        mock_should_update.assert_any_call('chant', config_file)
        mock_should_update.assert_any_call('source', config_file)
        mock_should_update.assert_any_call('provenance', config_file)
        # download_update()
        mock_dl_update.assert_any_call('chant', config_file)
        mock_dl_update.assert_any_call('source', config_file)
        # process_and_submit_updates()
        mock_pasu.assert_called_once_with(['downloaded chant'], config_file)
        # update_save_config()
        mock_usconf.assert_called_once_with(['chant', 'source'], ['source'], config_file, config_path)
