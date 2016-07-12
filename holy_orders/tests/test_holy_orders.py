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
import sqlite3
import tempfile
import unittest
from unittest import mock
from xml.etree import ElementTree as etree

import pytest

from tornado import httpclient

from hypothesis import assume, given, strategies as strats

from holy_orders import current, __main__ as holy_orders


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


@pytest.fixture()
def base_config(tmpdir):
    '''
    Make a base configuration for testing main(). It has one resource type ("source") and the
    database has a last update for it at 1987-09-09T10:36:00-04:00.

    :param tmpdir: A fixture form pytest.
    :returns: A two-tuplet with the path to the INI file and the path to the database.
    '''
    # set time for last update
    last_update = '1987-09-09T10:36:00-04:00'
    # prepare the updates database
    path_to_updates_db = os.path.join(str(tmpdir), 'updates.db')
    updates_db = sqlite3.connect(path_to_updates_db)
    updates_db.cursor().execute('CREATE TABLE rtypes (id INTEGER PRIMARY KEY,name TEXT,updated TEXT);')
    updates_db.cursor().execute('INSERT INTO rtypes (id, name, updated) VALUES (2, "source", ?);', (last_update,))
    updates_db.commit()
    updates_db.close()
    # prepare the configuration file
    ini_file = '''
    [general]
    resource_types = source
    solr_url = http://solr.example.com:8983/solr/collection1
    updates_db = {0}
    [update_frequency]
    source = 1d
    [drupal_urls]
    drupal_url = http://cantus.example.com
    source = %(drupal_url)s/export-sources
    '''.format(path_to_updates_db)
    path_to_ini = os.path.join(str(tmpdir), 'config.ini')
    with open(path_to_ini, 'w') as configfile:
        configfile.write(ini_file)

    return path_to_ini, path_to_updates_db


class TestMain(object):
    '''
    Tests for main().
    '''

    @mock.patch('holy_orders.__main__.download_update')
    @mock.patch('holy_orders.__main__.process_and_submit_updates')
    @mock.patch('holy_orders.__main__.commit_then_optimize')
    def test_main_1(self, mock_commit, mock_process, mock_download, base_config):
        '''
        There's one resource type ("source") and it:
        - doesn't need to be updated

        NB: tmpdir is a built-in pytest fixture.
        '''
        path_to_ini, path_to_updates_db = base_config
        # set what time "now" is---not using _now_wrapper()
        now = datetime.datetime.now(datetime.timezone.utc)
        current.update_db(sqlite3.connect(path_to_updates_db), 'source', now)
        now = now.isoformat()
        # prepare mock on download_updates()
        # NB: unnecessary
        # prepare mock on process_and_submit_updates()
        # NB: unnecessary

        # run the test
        holy_orders.main(path_to_ini)

        # check the mocks were called correctly
        assert mock_download.call_count == 0
        assert mock_process.call_count == 0
        mock_commit.assert_called_once_with('http://solr.example.com:8983/solr/collection1')
        # check the updates database is correct
        updates_db = sqlite3.connect(path_to_updates_db)
        assert current.get_last_updated(updates_db, 'source').isoformat() == now

    @mock.patch('holy_orders.__main__.download_update')
    @mock.patch('holy_orders.__main__.process_and_submit_updates')
    @mock.patch('holy_orders.__main__.commit_then_optimize')
    def test_main_2(self, mock_commit, mock_process, mock_download, base_config):
        '''
        There's one resource type ("source") and it:
        - fails during download_update()

        NB: tmpdir is a built-in pytest fixture.
        '''
        path_to_ini, path_to_updates_db = base_config
        # set time for last update
        last_update = '1987-09-09T10:36:00-04:00'
        # prepare mock on download_updates()
        mock_download.return_value = []
        # prepare mock on process_and_submit_updates()
        # NB: unnecessary

        # run the test
        holy_orders.main(path_to_ini)

        # check the mocks were called correctly
        mock_download.assert_called_once_with('source', mock.ANY)
        assert isinstance(mock_download.call_args_list[0][0][1], configparser.ConfigParser)
        assert mock_process.call_count == 0
        mock_commit.assert_called_once_with('http://solr.example.com:8983/solr/collection1')
        # check the updates database is correct
        updates_db = sqlite3.connect(path_to_updates_db)
        assert current.get_last_updated(updates_db, 'source').isoformat() == last_update

    @mock.patch('holy_orders.__main__.download_update')
    @mock.patch('holy_orders.__main__.process_and_submit_updates')
    @mock.patch('holy_orders.__main__.commit_then_optimize')
    def test_main_3(self, mock_commit, mock_process, mock_download, base_config):
        '''
        There's one resource type ("source") and it:
        - fails during process_and_submit_updates()

        NB: tmpdir is a built-in pytest fixture.
        '''
        path_to_ini, path_to_updates_db = base_config
        # set time for last update
        last_update = '1987-09-09T10:36:00-04:00'
        # prepare mock on download_updates()
        mock_download.return_value = ['upd']
        # prepare mock on process_and_submit_updates()
        mock_process.return_value = False

        # run the test
        holy_orders.main(path_to_ini)

        # check the mocks were called correctly
        mock_download.assert_called_once_with('source', mock.ANY)
        assert isinstance(mock_download.call_args_list[0][0][1], configparser.ConfigParser)
        mock_process.assert_called_once_with(mock_download.return_value, mock.ANY)
        assert isinstance(mock_process.call_args_list[0][0][1], configparser.ConfigParser)
        mock_commit.assert_called_once_with('http://solr.example.com:8983/solr/collection1')
        # check the updates database is correct
        updates_db = sqlite3.connect(path_to_updates_db)
        assert current.get_last_updated(updates_db, 'source').isoformat() == last_update

    @mock.patch('holy_orders.__main__.download_update')
    @mock.patch('holy_orders.__main__.process_and_submit_updates')
    @mock.patch('holy_orders.__main__.commit_then_optimize')
    def test_main_4(self, mock_commit, mock_process, mock_download, base_config):
        '''
        There's one resource type ("source") and it:
        - fails in an unexpected way (uses try/except in main() itself)

        NB: tmpdir is a built-in pytest fixture.
        '''
        path_to_ini, path_to_updates_db = base_config
        # set time for last update
        last_update = '1987-09-09T10:36:00-04:00'
        # prepare mock on download_updates()
        mock_download.side_effect = RuntimeError('it broke!')  # NB: this causes the failure
        # prepare mock on process_and_submit_updates()
        # NB: unnecessary

        # run the test
        holy_orders.main(path_to_ini)

        # check the mocks were called correctly
        mock_download.assert_called_once_with('source', mock.ANY)
        assert isinstance(mock_download.call_args_list[0][0][1], configparser.ConfigParser)
        assert mock_process.call_count == 0
        mock_commit.assert_called_once_with('http://solr.example.com:8983/solr/collection1')
        # check the updates database is correct
        updates_db = sqlite3.connect(path_to_updates_db)
        assert current.get_last_updated(updates_db, 'source').isoformat() == last_update

    @mock.patch('holy_orders.__main__.download_update')
    @mock.patch('holy_orders.__main__.process_and_submit_updates')
    @mock.patch('holy_orders.__main__.commit_then_optimize')
    def test_main_5(self, mock_commit, mock_process, mock_download, base_config):
        '''
        There's one resource type ("source") and it:
        - succeeds

        NB: tmpdir is a built-in pytest fixture.
        '''
        path_to_ini, path_to_updates_db = base_config
        # set time for last update
        now = datetime.datetime.now(datetime.timezone.utc)
        last_update = '1987-09-09T10:36:00-04:00'
        # prepare mock on download_updates()
        mock_download.return_value = ['upd']
        # prepare mock on process_and_submit_updates()
        mock_process.return_value = True

        # run the test
        holy_orders.main(path_to_ini)

        # check the mocks were called correctly
        mock_download.assert_called_once_with('source', mock.ANY)
        assert isinstance(mock_download.call_args_list[0][0][1], configparser.ConfigParser)
        mock_process.assert_called_once_with(mock_download.return_value, mock.ANY)
        assert isinstance(mock_process.call_args_list[0][0][1], configparser.ConfigParser)
        mock_commit.assert_called_once_with('http://solr.example.com:8983/solr/collection1')
        # check the updates database is correct (should be enough to check year, month, and day)
        new_time = current.get_last_updated(sqlite3.connect(path_to_updates_db), 'source')
        assert new_time.year == now.year
        assert new_time.month == now.month
        assert new_time.day == now.day


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
    @mock.patch('holy_orders.current.calculate_chant_updates')
    @mock.patch('holy_orders.__main__._collect_chant_ids')
    def test_download_chant_updates_1(self, mock_colids, mock_calcup, mock_download):
        '''
        Make sure it works.
        '''
        config = configparser.ConfigParser()
        config['drupal_urls'] = {'chants_updated': 'a/b/{date}', 'chant_id': 'a/c/{id}'}
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
    @mock.patch('holy_orders.current.calculate_chant_updates')
    def test_download_chant_updates_2(self, mock_calcup, mock_download):
        '''
        download_chant_updates() returns empty list when given bad "chants_updated"
        '''
        config = configparser.ConfigParser()
        config['drupal_urls'] = {'chants_updated': 'a/b/{}', 'chant_id': 'a/c/{id}'}
        expected = []

        actual = holy_orders.download_chant_updates(config)

        self.assertEqual(expected, actual)
        self.assertEqual(0, mock_download.call_count)
        self.assertEqual(0, mock_calcup.call_count)

    @mock.patch('holy_orders.__main__.download_from_urls')
    @mock.patch('holy_orders.current.calculate_chant_updates')
    @mock.patch('holy_orders.__main__._collect_chant_ids')
    def test_download_chant_updates_3(self, mock_colids, mock_calcup, mock_download):
        '''
        download_chant_updates() returns empty list when given bad "chant_id"
        '''
        config = configparser.ConfigParser()
        config['drupal_urls'] = {'chants_updated': 'a/b/{date}', 'chant_id': 'a/c/{}'}
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
        download_update() with 'chant' (it should call download_chant_updates())
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
        config = configparser.ConfigParser()
        config['drupal_urls'] = {'drupal_url': 'a', 'feast': 'a/b'}
        mock_urls.return_value = 42

        actual = holy_orders.download_update(resource_type, config)

        self.assertEqual(mock_urls.return_value, actual)
        mock_urls.assert_called_once_with(['a/b'])
        self.assertEqual(0, mock_chants.call_count)

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
