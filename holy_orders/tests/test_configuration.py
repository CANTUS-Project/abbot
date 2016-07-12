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
import pathlib
import sqlite3
import tempfile
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


class TestVerify(object):
    '''
    Tests for configuration.verify().
    '''

    def test_1(self):
        '''
        The file is valid.
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant,feast,genre,source', 'solr_url': 'http://solr',
            'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h', 'feast': '2h', 'genre': '3h', 'source': '4h'}
        config['drupal_urls'] = {
            'drupal_url': '444',
            'chants_updated': '444/chantup/{date}',
            'chant_id': '444/chantid/{id}',
            'feast': '444/feast',
            'genre': '444/jean',
            'source': '444/source'
        }

        assert configuration.verify(config) is config

    def test_2(self):
        '''
        Fail with this check:
        - the "general," "update_frequency," and "drupal_urls" sections are all defined
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant,feast,genre,source', 'solr_url': 'http://solr',
            'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h', 'feast': '2h', 'genre': '3h', 'source': '4h'}

        with pytest.raises(KeyError):
            configuration.verify(config)

    def test_3(self):
        '''
        Fail with this check:
        - "resource_types" is defined in "general" as a comma-separated set of lowercase ASCII names
          separated by commas
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': '14', 'solr_url': 'http://solr',
            'updates_db': 'something.db'}
        config['update_frequency'] = {'source': '4h'}
        config['drupal_urls'] = {'drupal_url': '444', 'source': '444/source'}

        with pytest.raises(ValueError):
            configuration.verify(config)

    def test_4(self):
        '''
        Fail with this check:
        - "solr_url" is defined in "general"
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'source', 'updates_db': 'something.db'}
        config['update_frequency'] = {'source': '4h'}
        config['drupal_urls'] = {'drupal_url': '444', 'source': '444/source'}

        with pytest.raises(KeyError):
            configuration.verify(config)

    def test_4_1(self):
        '''
        Fail with this check:
        - "updates_db" is defined in "general"
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'source', 'solr_url': 'http://solr'}
        config['update_frequency'] = {'source': '4h'}
        config['drupal_urls'] = {'drupal_url': '444', 'source': '444/source'}

        with pytest.raises(KeyError):
            configuration.verify(config)

    def test_5(self):
        '''
        Fail with this check:
        - "drupal_url" is defined in "drupal_urls"
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant,feast,genre,source', 'solr_url': 'http://solr',
            'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h', 'feast': '2h', 'genre': '3h', 'source': '4h'}
        config['drupal_urls'] = {
            'chants_updated': '444/chantup/{date}',
            'chant_id': '444/chantid/{id}',
            'feast': '444/feast',
            'genre': '444/jean',
            'source': '444/source'
        }

        with pytest.raises(KeyError):
            configuration.verify(config)

    def test_6(self):
        '''
        Fail with this check:
        - every resource type has an entry in the "update_frequency" section
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant,feast,genre,source', 'solr_url': 'http://solr',
            'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h', 'feast': '2h', 'genre': '3h'}  # missing "source"
        config['drupal_urls'] = {
            'drupal_url': '444',
            'chants_updated': '444/chantup/{date}',
            'chant_id': '444/chantid/{id}',
            'feast': '444/feast',
            'genre': '444/jean',
            'source': '444/source'
        }

        with pytest.raises(KeyError):
            configuration.verify(config)

    def test_7(self):
        '''
        Fail with this check:
        - every resource type has an entry in the "drupal_urls" section
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant,feast,genre,source', 'solr_url': 'http://solr',
            'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h', 'feast': '2h', 'genre': '3h', 'source': '4h'}
        config['drupal_urls'] = {
            'drupal_url': '444',
            'chants_updated': '444/chantup/{date}',
            'chant_id': '444/chantid/{id}',
            'feast': '444/feast',
            'genre': '444/jean',
            # missing "source"
        }

        with pytest.raises(KeyError):
            configuration.verify(config)

    def test_8(self):
        '''
        Fail with this check:
        - every "drupal_urls" entry begins with the value of "drupal_url"
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant,feast,genre,source', 'solr_url': 'http://solr',
            'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h', 'feast': '2h', 'genre': '3h', 'source': '4h'}
        config['drupal_urls'] = {
            'drupal_url': '444',
            'chants_updated': '444/chantup/{date}',
            'chant_id': '444/chantid/{id}',
            'feast': '/feast',  # purposely missing the "444"
            'genre': '444/jean',
            'source': '444/source'
        }

        with pytest.raises(ValueError):
            configuration.verify(config)

    def test_9a(self):
        '''
        Fail with this check:
        - if "chant" is in "resource_types" then "chants_updated" and "chant_id" URLs are in the
          "drupal_urls" section rather than "chant", containing "{date}" and "{id}" respectively

        (one of the URLs is missing)
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant', 'solr_url': 'http://solr', 'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h'}
        config['drupal_urls'] = {'drupal_url': '444', 'chants_updated': '444/chantup/{date}'}

        with pytest.raises(KeyError):
            configuration.verify(config)

    def test_9b(self):
        '''
        Fail with this check:
        - if "chant" is in "resource_types" then "chants_updated" and "chant_id" URLs are in the
          "drupal_urls" section rather than "chant", containing "{date}" and "{id}" respectively

        (substitution keyword is missing from "chants_updated")
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant', 'solr_url': 'http://solr', 'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h'}
        config['drupal_urls'] = {'drupal_url': '444', 'chants_updated': '444/chantup', 'chant_id': '444/chantid/{id}'}

        with pytest.raises(ValueError):
            configuration.verify(config)

    def test_9c(self):
        '''
        Fail with this check:
        - if "chant" is in "resource_types" then "chants_updated" and "chant_id" URLs are in the
          "drupal_urls" section rather than "chant", containing "{date}" and "{id}" respectively

        (substitution keyword is missing from "chant_id")
        '''
        config = configparser.ConfigParser()
        config['general'] = {'resource_types': 'chant', 'solr_url': 'http://solr', 'updates_db': 'something.db'}
        config['update_frequency'] = {'chant': '1h'}
        config['drupal_urls'] = {'drupal_url': '444', 'chants_updated': '444/chantup/{date}', 'chant_id': '444/chantid/'}

        with pytest.raises(ValueError):
            configuration.verify(config)


class TestLoadDb(object):
    '''
    Tests for load_db().
    '''

    def test_works(self, tmpdir):
        '''
        When the configured path leads to a file that exists and is loaded.
        NB: "tmpdir" is a pytest fixture
        '''
        db_path = os.path.join(str(tmpdir), 'updates.db')
        with open(db_path, 'w') as db:
            db.write('something')
        config = configparser.ConfigParser()
        config['general'] = {'updates_db': db_path}

        actual = configuration.load_db(config)
        assert actual[0] is config
        assert isinstance(actual[1], sqlite3.Connection)

    def test_not_exist(self):
        '''
        When the configured path doesn't exist.
        '''
        config = configparser.ConfigParser()
        config['general'] = {'updates_db': '/broccoli/washer.db'}
        with pytest.raises(RuntimeError):
            configuration.load_db(config)

    def test_not_file(self):
        '''
        When the configured path exists but is not a file.
        '''
        config = configparser.ConfigParser()
        config['general'] = {'updates_db': '/etc'}
        with pytest.raises(RuntimeError):
            configuration.load_db(config)
