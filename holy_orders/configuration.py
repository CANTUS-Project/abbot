#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           holy_orders
# Program Description:    Update program for the Abbot Cantus API server.
#
# Filename:               holy_orders/configuration.py
# Purpose:                Configuration management for Holy Orders.
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
Configuration management for Holy Orders.
'''

import datetime
import json
import pathlib

# set up logging
import tornado.log
_log = tornado.log.app_log


def _now_wrapper():
    '''
    A wrapper function for datetime.datetime.utcnow() that can be mocked for automated tests.
    '''
    return datetime.datetime.now(datetime.timezone.utc)


def update_save_config(to_update, failed_types, config, config_path):
    '''
    Update the "last updated" times in the configuration file, taking into account the types that
    required an update and which of those failed to be updated for some reason. Then save the
    updated configuration object.

    :param to_update: A list of the types that we tried to update.
    :type to_update: list of str
    :param failed_types: A list of the types that we tried to update but couldn't.
    :type failed_types: list of str
    :param dict config: Dictionary of the configuration file that has our data.
    :returns: An updated version of ``config``.
    :rtype: dict
    :raises: :exc:`OSError` when the file cannot be written.
    :raises: :exc:`IOError` when the file cannot be written.
    '''

    for each_type in to_update:
        if each_type not in failed_types:
            _log.info('Updating "last update" time for {}'.format(each_type))
            config['last_updated'][each_type] = _now_wrapper().timestamp()
        else:
            _log.error('Failed to update "{}" resources!'.format(each_type))

    _log.info('Saving configuration file')
    with open(config_path, 'w') as fp:
        json.dump(config, fp, indent='\t', sort_keys=True)


def load_config(config_path):
    '''
    Given the path to a "Holy Orders" configuration file, load the file and check that the conversion
    script from Drupal XML to Solr XML is present ans seems to work.

    :param str config_path: Pathname to the "Holy Orders" configuration file.
    :returns: The configuration file's contents.
    :rtype: dict
    '''

    config_path = pathlib.Path(config_path)
    try:
        if not (config_path.exists() and config_path.is_file()):
            _log.error('Please provide the path to a valid JSON file for configuration.')
            raise SystemExit(1)
    except OSError:
        # e.g., the file name is too long
        _log.error('Please provide the path to a valid JSON file for configuration.')
        raise SystemExit(1)

    try:
        with config_path.open() as config_file:
            config = json.load(config_file)
    except ValueError as val_err:
        _log.error('JSON configuration file failed to load.\n{}'.format(val_err.args[0]))
        raise SystemExit(1)

    return config
