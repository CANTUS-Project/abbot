#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               holy_orders/make_database.py
# Purpose:                Make an empty "updates database" file.
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
Make an empty "updates database" file.
'''

import configparser
import pathlib
import sqlite3
import sys


def _load(config_path):
    # NOTE: keep this in sync with the copy in "configuration.py"

    config = configparser.ConfigParser()
    files_read = config.read(config_path)

    if len(files_read) == 0:
        err_msg = 'Could not open INI configuration file:\n{0}'.format(config_path)
        _log.error(err_msg)
        raise RuntimeError(err_msg)

    return config


def _verify(config):
    # NOTE: keep this in sync with the copy in "configuration.py"

    # - the "general," "update_frequency," and "drupal_urls" sections are all defined
    if 'general' not in config or 'update_frequency' not in config or 'drupal_urls' not in config:
        raise KeyError('Missing section: general, update_frequency, or drupal_urls.')

    # - "resource_types" is defined in "general" as a comma-separated set of lowercase ASCII names
    #   separated by commas
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz,'
    for each_char in config['general']['resource_types']:
        if each_char not in allowed_chars:
            raise ValueError('Invalid "resource_types" value.')

    # - "solr_url" is defined in "general"
    if 'solr_url' not in config['general']:
        raise KeyError('Missing "solr_url" setting')

    # - "updates_db" is defined in "general"
    if 'updates_db' not in config['general']:
        raise KeyError('Missing "updates_db" setting')

    # - "drupal_url" is defined in "drupal_urls"
    if 'drupal_url' not in config['drupal_urls']:
        raise KeyError('Missing "drupal_url" setting in "drupal_urls" section')

    # - every resource type has an entry in the "update_frequency" section
    for rtype in config['general']['resource_types'].split(','):
        if rtype not in config['update_frequency']:
            raise KeyError('Missing "{0}" setting in "update_frequency" section'.format(rtype))

    # - every resource type has an entry in the "drupal_urls" section
    for rtype in config['general']['resource_types'].split(','):
        if rtype != 'chant' and rtype not in config['drupal_urls']:
            raise KeyError('Missing "{0}" setting in "drupal_urls" section'.format(rtype))

    # - every "drupal_urls" entry begins with the value of "drupal_url"
    drupal_url = config['drupal_urls']['drupal_url']
    for url in config['drupal_urls']:
        if url != 'drupal_url' and not config['drupal_urls'][url].startswith(drupal_url):
            raise ValueError('Drupal URL for {0} does not start with the URL to Drupal.'.format(url))

    # - if "chant" is in "resource_types" then "chants_updated" and "chant_id" URLs are in the
    #   "drupal_urls" section rather than "chant", containing "{date}" and "{id}" respectively
    if 'chant' in config['general']['resource_types'].split(','):
        if 'chants_updated' not in config['drupal_urls'] or 'chant_id' not in config['drupal_urls']:
            raise KeyError('Missing Drupal URL for chants.')
        if '{date}' not in config['drupal_urls']['chants_updated']:
            raise ValueError('Missing "{date}" part of "chants_updated" Drupal URL')
        if '{id}' not in config['drupal_urls']['chant_id']:
            raise ValueError('Missing "{id}" part of "chant_id" Drupal URL')

    return config


def check_path(db_path):
    '''
    Raise an exception if the :class:`Path` to the updates database isn't good.

    :param db_path: The path to the updates database file.
    :type db_path: :class:`pathlib.Path`
    :raises: :exc:`RuntimeError` if the file already exists.
    :raises: :exc:`RuntimeError` if the file is not in a directory that already exists.
    '''
    db_path_parent = db_path.parent
    if db_path.exists():
        raise RuntimeError('Updates database already exists; cannot make a new one.')
    elif not (db_path_parent.exists() and db_path_parent.is_dir()):
        raise RuntimeError('Path to updates database must be in a directory that already exists.')


def make_rtypes_table(conn, rtypes):
    '''
    Make the "ryptes" database table and fill it with records for the indicated resource types.

    :param conn: An open connection to the SQLite database.
    :type conn: :class:`sqlite3.Connection`
    :param ryptes: The required resource types.
    :type rtypes: list of str
    '''
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE rtypes (id INTEGER PRIMARY KEY, name TEXT, updated TEXT);')
    for i, rtype in enumerate(rtypes):
        cursor.execute(
            'INSERT INTO rtypes (id, name, updated) VALUES (?, ?, "never");',
            (i, rtype))

    conn.commit()


def main(ini_path):
    '''
    Create a new database according to the settings in "ini_path."
    '''
    config = _verify(_load(ini_path))
    db_path = pathlib.Path(config['general']['updates_db'])

    check_path(db_path)

    conn = sqlite3.Connection(str(db_path))
    make_rtypes_table(conn, config['general']['resource_types'].split(','))


if __name__ == '__main__':
    if 'python' in sys.argv[0]:
        main(sys.argv[2])
    else:
        main(sys.argv[1])
