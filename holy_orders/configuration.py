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

import configparser
import datetime
import json

# set up logging
import tornado.log
_log = tornado.log.app_log


# translatable strings
_OPEN_INI_ERROR = 'Could not open INI configuration file:\n{0}'


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
    :param config: The configuration file that has our data.
    :type config: :class:`configparser.ConfigParser`
    :returns: The updated of ``config``.
    :rtype: :class:`configparser.ConfigParser`
    :raises: :exc:`OSError` subclass when the file cannot be written for some reason.
    '''

    for each_type in to_update:
        if each_type in failed_types:
            _log.error('Failed to update "{}" resources!'.format(each_type))
        else:
            _log.info('Updating "last update" time for {}'.format(each_type))
            config['last_updated'][each_type] = str(_now_wrapper().timestamp())

    _log.info('Saving configuration file')
    with open(config_path, 'w') as fp:
        config.write(fp)

    return config


def load(config_path):
    '''
    Load a "Holy Orders" configuration file in INI format.

    :param str config_path: Pathname to the "Holy Orders" configuration file.
    :returns: The configuration file.
    :rtype: :class:`configparser.ConfigParser`
    :raises: :exc:`configparser.Error` when the configuration file is invalid.
    :raises: :exc:`RuntimeError` when `config_path` doesn't exist or similar.
    '''

    config = configparser.ConfigParser()
    files_read = config.read(config_path)

    if len(files_read) == 0:
        err_msg = _OPEN_INI_ERROR.format(config_path)
        _log.error(err_msg)
        raise RuntimeError(err_msg)

    return config


def verify(config):
    '''
    Verify a HolyOrders configuration file.

    :param config: The configuration file.
    :type config: :class:`configparser.ConfigParser`
    :returns: The configuration file.
    :rtype: :class:`configparser.ConfigParser`
    :raises: :exc:`KeyError` when the configuration file is missing required values.
    :raises: :exc:`ValueError` when a configuration value is incorrect.

    The following characteristics are verified:

    - the "general," "update_frequency," and "drupal_urls" sections are all defined
    - "resource_types" is defined in "general" as a comma-separated set of lowercase ASCII names
      separated by commas
    - "solr_url" is defined in "general"
    - "updates_db" is defined in "general"
    - "drupal_url" is defined in "drupal_urls"
    - every resource type has an entry in the "update_frequency" section
    - every resource type has an entry in the "drupal_urls" section
    - every "drupal_urls" entry begins with the value of "drupal_url"
    - if "chant" is in "resource_types" then "chants_updated" and "chant_id" URLs are in the
      "drupal_urls" section rather than "chant", containing "{date}" and "{id}" respectively
    '''
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
