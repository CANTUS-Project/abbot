#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               holy_orders/tests/make_database.py
# Purpose:                Tests for the "make_database.py" script.
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
Tests for the "make_database.py" script.
'''

import os.path
import pathlib
import sqlite3
import subprocess
import sys

import pytest

from holy_orders import make_database


class TestCheckPath(object):
    '''
    Tests for check_path().
    '''

    def test_works(self, tmpdir):
        '''
        When the file is in a directory that exists.
        '''
        db_path = pathlib.Path(str(tmpdir), 'ffffffffffff.db')
        make_database.check_path(db_path)

    def test_already_exists(self, tmpdir):
        '''
        When the file already exists.
        '''
        db_path = pathlib.Path(str(tmpdir), 'ffffffffffff.db')
        db_path.touch()
        with pytest.raises(RuntimeError):
            make_database.check_path(db_path)

    def test_parent_not_exist(self, tmpdir):
        '''
        When the parent directory doesn't exist.
        '''
        db_path = pathlib.Path(str(tmpdir), 'whatever', 'ffffffffffff.db')
        with pytest.raises(RuntimeError):
            make_database.check_path(db_path)

    def test_parent_is_file(self, tmpdir):
        '''
        When the parent directory exists, but it's actually a file.
        '''
        db_path = pathlib.Path(str(tmpdir), 'whatever', 'ffffffffffff.db')
        db_path.parent.touch()
        with pytest.raises(RuntimeError):
            make_database.check_path(db_path)


def test_make_rtypes_table():
    conn = sqlite3.Connection(':memory:')
    rtypes = ['trunk', 'branch', 'leaf']

    make_database.make_rtypes_table(conn, rtypes)

    records = conn.cursor().execute('SELECT * FROM rtypes').fetchall()
    assert len(records) == len(rtypes)
    for _, rtype, updated in records:
        assert rtype in rtypes
        assert updated == 'never'


def test_main_1(tmpdir):
    '''
    When main() is called directly.
    '''
    path_to_updates_db = os.path.join(str(tmpdir), 'updates.db')
    # prepare the configuration file
    ini_file = '''
    [general]
    resource_types = trunk,branch,leaf
    solr_url = http://solr.example.com:8983/solr/collection1
    updates_db = {0}

    [update_frequency]
    trunk = 1d
    branch = 1d
    leaf = 1d

    [drupal_urls]
    drupal_url = http://trees.example.org
    trunk = %(drupal_url)s/export-trunks
    branch = %(drupal_url)s/export-branches
    leaf = %(drupal_url)s/export-leaves
    '''.format(path_to_updates_db)
    path_to_ini = os.path.join(str(tmpdir), 'config.ini')
    with open(path_to_ini, 'w') as configfile:
        configfile.write(ini_file)

    make_database.main(path_to_ini)

    rtypes = ('trunk', 'branch', 'leaf')
    conn = sqlite3.Connection(path_to_updates_db)
    records = conn.cursor().execute('SELECT * FROM rtypes').fetchall()
    assert len(records) == len(rtypes)
    for _, rtype, updated in records:
        assert rtype in rtypes
        assert updated == 'never'


def test_main_2(tmpdir):
    '''
    When the script is executed as "python make_database.py whatever_path.ini"
    '''
    path_to_updates_db = os.path.join(str(tmpdir), 'updates.db')
    # prepare the configuration file
    ini_file = '''
    [general]
    resource_types = trunk
    solr_url = http://solr.example.com:8983/solr/collection1
    updates_db = {0}
    [update_frequency]
    trunk = 1d
    [drupal_urls]
    drupal_url = http://trees.example.org
    trunk = %(drupal_url)s/export-trunks
    '''.format(path_to_updates_db)
    path_to_ini = os.path.join(str(tmpdir), 'config.ini')
    with open(path_to_ini, 'w') as configfile:
        configfile.write(ini_file)

    script_file = pathlib.Path(os.path.split(__file__)[0], '..', 'make_database.py').resolve()
    subprocess.check_call([sys.executable, str(script_file), path_to_ini])

    rtypes = ('trunk', 'branch', 'leaf')
    assert pathlib.Path(path_to_updates_db).exists()


def test_main_3(tmpdir):
    '''
    When the script is executed as "make_database.py whatever_path.ini"
    '''
    path_to_updates_db = os.path.join(str(tmpdir), 'updates.db')
    # prepare the configuration file
    ini_file = '''
    [general]
    resource_types = trunk
    solr_url = http://solr.example.com:8983/solr/collection1
    updates_db = {0}
    [update_frequency]
    trunk = 1d
    [drupal_urls]
    drupal_url = http://trees.example.org
    trunk = %(drupal_url)s/export-trunks
    '''.format(path_to_updates_db)
    path_to_ini = os.path.join(str(tmpdir), 'config.ini')
    with open(path_to_ini, 'w') as configfile:
        configfile.write(ini_file)

    script_file = pathlib.Path(os.path.split(__file__)[0], '..', 'make_database.py').resolve()
    subprocess.check_call([str(script_file), path_to_ini])

    rtypes = ('trunk', 'branch', 'leaf')
    assert pathlib.Path(path_to_updates_db).exists()
