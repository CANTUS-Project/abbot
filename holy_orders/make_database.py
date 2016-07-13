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

import pathlib
import sqlite3
import sys

from holy_orders import configuration


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
    config = configuration.verify(configuration.load(ini_path))
    db_path = pathlib.Path(config['general']['updates_db'])

    check_path(db_path)

    conn = sqlite3.Connection(str(db_path))
    make_rtypes_table(conn, config['general']['resource_types'].split(','))


if __name__ == '__main__':
    if 'python' in sys.argv[0]:
        main(sys.argv[2])
    else:
        main(sys.argv[1])
