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

# pylint: disable=protected-access
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

import configparser
import datetime
import json
import os.path
import pathlib
import tempfile
import unittest
from unittest import mock
from xml.etree import ElementTree as etree

from tornado import httpclient

from hypothesis import assume, given, strategies as strats

import holy_orders.__main__ as holy_orders


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
        self.assertRaises(KeyError, holy_orders.should_update_this, resource_type, config)

    def test_should_update_2(self):
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
        solr_url = 'http::/com.checkit/'
        exp_update_url = '{}update?commit=false'.format(solr_url)
        update = etree.Element('something', {'funlevel': 'wöo'})
        update_body = '<something funlevel="wöo" />'
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()

        holy_orders.submit_update(update, solr_url)

        mock_client.fetch.assert_called_once_with(exp_update_url, method='POST', body=update_body,
                                                  headers={'Content-Type': 'application/xml'})

    @mock.patch('holy_orders.__main__.httpclient')
    def test_solr_is_borked(self, mock_httpclient):
        '''
        submit_update() when Solr doesn't like the update, and the submission URL does not end with
        a trailing slash.
        '''
        update_pathname = '123abc.xml'
        solr_url = 'http::/com.trailingslash'
        exp_update_url = '{}/update?commit=false'.format(solr_url)
        update = etree.Element('something', {'funlevel': 'wöo'})
        update_body = '<something funlevel="wöo" />'
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()
        mock_client.fetch.side_effect = IOError('whatever, man')

        self.assertRaises(RuntimeError, holy_orders.submit_update, update, solr_url)

        mock_client.fetch.assert_called_once_with(exp_update_url, method='POST', body=update_body,
                                                  headers={'Content-Type': 'application/xml'})


class TestProcessAndSubmitUpdates(unittest.TestCase):
    '''
    Tests for process_and_submit_updates().
    '''

    @mock.patch('holy_orders.drupal_to_solr.convert')
    @mock.patch('holy_orders.__main__.submit_update')
    def test_everything_works(self, mock_submit, mock_convert):
        '''
        everything works
        '''
        config = {'solr_url': 'http://solr.com'}
        updates = ['update one', 'update two', 'update three']
        converted = ['converted one', 'converted two', 'converted three']
        mock_convert_returns = ['converted one', 'converted two', 'converted three']
        mock_convert.side_effect = lambda *args: mock_convert_returns.pop()
        expected = True

        actual = holy_orders.process_and_submit_updates(updates, config)

        assert expected is actual
        assert len(updates) == mock_convert.call_count
        for i, _ in enumerate(updates):
            mock_convert.assert_any_call(updates[i])
        assert len(converted) == mock_submit.call_count
        for i, _ in enumerate(converted):
            mock_submit.assert_any_call(converted[i], config['solr_url'])

    @mock.patch('holy_orders.drupal_to_solr.convert')
    @mock.patch('holy_orders.__main__.submit_update')
    def test_conversion_fails(self, mock_submit, mock_convert):
        '''
        everything else works when convert_update() fails with one
        '''
        config = {'solr_url': 'http://solr.com'}
        updates = ['update one', 'update two', 'update three']
        converted = ['converted one', 'converted three']
        mock_convert_returns = ['converted one', RuntimeError('yuck'), 'converted three']
        def convert_mocker(*args):  # pylint: disable=unused-argument
            "Mocks convert()."
            zell = mock_convert_returns.pop()
            if isinstance(zell, str):
                return zell
            else:
                raise zell
        mock_convert.side_effect = convert_mocker
        expected = False

        actual = holy_orders.process_and_submit_updates(updates, config)

        assert expected is actual
        assert len(updates) == mock_convert.call_count
        for i, _ in enumerate(updates):
            mock_convert.assert_any_call(updates[i])
        assert len(converted) == mock_submit.call_count
        for i, _ in enumerate(converted):
            mock_submit.assert_any_call(converted[i], config['solr_url'])

    @mock.patch('holy_orders.drupal_to_solr.convert')
    @mock.patch('holy_orders.__main__.submit_update')
    def test_submission_fails(self, mock_submit, mock_convert):
        '''
        submit_update() fails with one
        '''
        config = {'solr_url': 'http://solr.com'}
        updates = ['update one', 'update two', 'update three']
        converted = ['converted one', 'converted two', 'converted three']
        mock_convert_returns = ['converted one', 'converted two', 'converted three']
        mock_convert.side_effect = lambda *args: mock_convert_returns.pop()
        mock_submit_returns = [None, RuntimeError('wow'), None]
        def submit_mocker(*args):  # pylint: disable=unused-argument
            "Mocks submit()."
            zell = mock_submit_returns.pop()
            if zell:
                raise zell
        mock_submit.side_effect = submit_mocker
        expected = False

        actual = holy_orders.process_and_submit_updates(updates, config)

        assert expected is actual
        assert len(updates) == mock_convert.call_count
        for i, _ in enumerate(updates):
            mock_convert.assert_any_call(updates[i])
        assert len(converted) == mock_submit.call_count
        for i, _ in enumerate(converted):
            mock_submit.assert_any_call(converted[i], config['solr_url'])


class TestMain(unittest.TestCase):
    '''
    Tests for main().
    '''

    @mock.patch('holy_orders.__main__.commit_then_optimize')
    @mock.patch('holy_orders.configuration.update_save_config')
    @mock.patch('holy_orders.__main__.process_and_submit_updates')
    @mock.patch('holy_orders.__main__.download_update')
    @mock.patch('holy_orders.__main__.should_update_this')
    def test_it_works(self, mock_should_update, mock_dl_update, mock_pasu, mock_usconf, mock_cto):
        '''
        When everything works (in that there are no exceptions).

        There are four resource types:
        - provenance, which doesn't need to be updated.
        - source, which fails during the call to download_update().
        - feast, which fails during the call to process_and_submit_updates().
        - chant, which works.
        '''
        config_path = os.path.join(os.path.split(__file__)[0], 'sample_config.ini')
        config_file = configparser.ConfigParser()
        config_file.read(config_path)
        # everything but "provenance" needs to be updated
        mock_should_update.side_effect = lambda x, y: False if x == 'provenance' else True
        # the "source" Drupal URL is missing in the config
        mock_dl_update.side_effect = lambda x, y: ['downloaded {}'.format(x)] if x == 'chant' else []
        # "feast" fails in process_and_submit_updates()
        def pasu_side_effect(updates, config):  # pylint: disable=unused-argument
            "process_and_submit_updates() side_effect function."
            return ['downloaded chant'] == updates
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
        # commit_then_optimize()
        mock_cto.assert_called_once_with(config_file['general']['solr_url'])


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
        xml_docs = ''.join(xml_docs)  # pylint: disable=redefined-variable-type
        xml_docs = [xml_docs]
        expected = set(list_of_ids)

        # run the test and check results
        actual = holy_orders._collect_chant_ids(xml_docs)
        self.assertCountEqual(expected, actual)

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
        xml_docs = ''.join(xml_docs)  # pylint: disable=redefined-variable-type
        xml_docs = bytes(xml_docs, 'UTF-8')
        xml_docs = [xml_docs]
        expected = set(list_of_ids)

        # run the test and check results
        actual = holy_orders._collect_chant_ids(xml_docs)
        self.assertCountEqual(expected, actual)

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
        for i in range(3):
            xml_docs.append('''<chants>
            <chant><id>{}1</id></chant>
            <chant><id>{}2</id></chant>
            <chant><id>{}3</id></chant>
            </chants>
            '''.format(i, i, i))
        expected = ['01', '02', '03', '11', '12', '13', '21', '22', '23']

        # run the test and check results
        actual = holy_orders._collect_chant_ids(xml_docs)
        self.assertCountEqual(expected, actual)

    def test_collect_ids_6(self):
        '''
        _collect_chant_ids() deduplicates chant IDs for update, so we only download a chant once
        '''
        xml_docs = ['<chants><chant><id>888</id></chant><chant><id>888</id></chant></chants>']
        actual = holy_orders._collect_chant_ids(xml_docs)
        assert ['888'] == actual

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
    def test_download_chant_updates_2(self, mock_calcup, mock_download):
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


class TestCommitThenOptimize(unittest.TestCase):
    '''
    Tests for holy_orders.__main__.commit_then_optimize().
    '''

    @mock.patch('holy_orders.__main__.httpclient')
    def test_everything_works(self, mock_httpclient):
        '''
        commit_then_optimize() when everything goes according to plan and the URL ends with a /
        '''
        solr_url = 'http::/com.checkit/'
        commit_url = '{}update?commit=true'.format(solr_url)
        optimize_url = '{}update?optimize=true'.format(solr_url)
        request_timeout = 5 * 60
        expected = 0
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()

        actual = holy_orders.commit_then_optimize(solr_url)

        assert expected == actual
        mock_client.fetch.assert_any_call(commit_url, method='GET', request_timeout=request_timeout)
        mock_client.fetch.assert_any_call(optimize_url, method='GET', request_timeout=request_timeout)
        mock_client.close.assert_called_once_with()

    @mock.patch('holy_orders.__main__.httpclient')
    def test_commit_fails(self, mock_httpclient):
        '''
        commit_then_optimize() when the commit fails and the URL doesn't end with a /
        '''
        solr_url = 'http::/com.checkit'
        commit_url = '{}/update?commit=true'.format(solr_url)
        # optimize_url = '{}/update?optimize=true'.format(solr_url)
        request_timeout = 5 * 60
        expected = 1
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock(side_effect=IOError)

        actual = holy_orders.commit_then_optimize(solr_url)

        assert expected == actual
        assert mock_client.fetch.call_count == 1
        mock_client.fetch.assert_any_call(commit_url, method='GET', request_timeout=request_timeout)
        mock_client.close.assert_called_once_with()

    @mock.patch('holy_orders.__main__.httpclient')
    def test_optimize_fails(self, mock_httpclient):
        '''
        commit_then_optimize() when the commit works but the optimize fails
        '''
        solr_url = 'http::/com.checkit/'
        commit_url = '{}update?commit=true'.format(solr_url)
        optimize_url = '{}update?optimize=true'.format(solr_url)
        request_timeout = 5 * 60
        expected = 2
        # setup the httpclient mock
        mock_httpclient.HTTPError = httpclient.HTTPError
        mock_client = mock.Mock()
        mock_httpclient.HTTPClient = mock.Mock()
        mock_httpclient.HTTPClient.return_value = mock_client
        mock_client.close = mock.Mock()
        mock_client.fetch = mock.Mock()
        # ugh...
        def fetch_side_effect(url, *args, **kwargs):  # pylint: disable=unused-argument
            "Raise IOError if 'commit' is not in 'url'."
            if 'commit' not in url:
                raise IOError()
        mock_client.fetch.side_effect = fetch_side_effect

        actual = holy_orders.commit_then_optimize(solr_url)

        assert expected == actual
        mock_client.fetch.assert_any_call(commit_url, method='GET', request_timeout=request_timeout)
        mock_client.fetch.assert_any_call(optimize_url, method='GET', request_timeout=request_timeout)
        mock_client.close.assert_called_once_with()
