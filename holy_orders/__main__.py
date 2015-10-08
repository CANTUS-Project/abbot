#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           holy_orders
# Program Description:    Update program for the Abbot Cantus API server.
#
# Filename:               holy_orders/__main__.py
# Purpose:                Main file for Holy Orders.
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
Main file for Holy Orders.

This program is responsible for updating the Solr database of an Abbot installation. The program's
name is inspired by a method of communication to abbots: through holy orders.
'''

import datetime
import json
import logging
import pathlib
import subprocess
from sys import argv
import tempfile

from systemdream.journal import handler as journalctl

from tornado import httpclient

# settings
LOG_LEVEL = logging.DEBUG


# script-level "globals"
_log = None


def _now_wrapper():
    '''
    A wrapper function for datetime.datetime.utcnow() that can be mocked for automated tests.
    '''
    return datetime.datetime.now(datetime.timezone.utc)


def main(config_path):
    '''
    Run Holy Orders. Perform an update of the Solr server running on localhost:8983.
    '''
    _set_up_logging()

    config = load_config(config_path)

    failed_types = []  # resource types that couldn't be updated for some reason

    _log.info('Checking which types to update')
    types_to_update = []
    for resource_type in config['resource_types']:
        yes_update = False

        try:
            yes_update = should_update_this(resource_type, config)
        except KeyError:
            failed_types.append(resource_type)

        if yes_update:
            types_to_update.append(resource_type)

    _log.info('Downloading updates')
    updates = []
    for resource_type in types_to_update:
        if resource_type in config['drupal_urls']:
            the_updates = download_update(resource_type, config)
            if len(the_updates) > 0:
                updates.extend(the_updates)
            else:
                _log.error('No updates donwloaded for {} resources!'.format(resource_type))
                failed_types.append(resource_type)
        else:
            _log.error('Missing Drupal URL for "{}" in configuration file! Not updating.'.format(resource_type))

    _log.info('Converting and submitting updates')
    process_and_submit_updates(updates, config)

    _log.info('Updating configuration file')
    try:
        update_save_config(types_to_update, failed_types, config, config_path)
    except (OSError, IOError) as err:
        _log.error('Unable to save updated configuration file: {}'.format(err))


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
    _set_up_logging()

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
    _set_up_logging()

    config_path = pathlib.Path(config_path)
    if not (config_path.exists() and config_path.is_file()):
        _log.error('Please provide the path to a valid JSON file for configuration.')
        raise SystemExit(1)

    try:
        with config_path.open() as config_file:
            config = json.load(config_file)
    except ValueError as val_err:
        _log.error('JSON configuration file failed to load.\n{}'.format(val_err.args[0]))
        raise SystemExit(1)

    return config


def process_and_submit_updates(updates, config):
    '''
    Given a list of updates from Drupal, convert the documents to Solr XML and submit them to Solr.

    :param updates: The updates from Drupal.
    :type updates: list of str
    :param dict config: Dictionary of the configuration file that has our data.
    :returns: Whether all the updates were successfully converted and submitted.
    :rtype: bool
    '''
    _set_up_logging()

    conversion_script_path = get_conversion_script_path(config)

    updates_have_failed = False
    with tempfile.TemporaryDirectory() as temp_directory:
        conversions_failed = False
        converted = []
        for update in updates:
            try:
                converted.append(convert_update(temp_directory, str(conversion_script_path), update))
            except RuntimeError:
                conversions_failed = True

        if conversions_failed:
            _log.error('At least some updates have failed during conversion to Solr XML!')
            updates_have_failed = True

        submissions_failed = False
        for update in converted:
            try:
                submit_update(update, config['solr_url'])
            except RuntimeError:
                submissions_failed = True

        if submissions_failed:
            _log.error('At least some updates have failed during uploading to Solr!')
            updates_have_failed = True

    return not updates_have_failed


def get_conversion_script_path(config):
    '''
    Given the "Holy Orders" configuration, validate and return the path to the Drupal-to-Solr
    conversion script.

    :param dict config: Dictionary of the configuration file that has our data.
    :returns: The path to the conversion script.
    :rtype: :class:`pathlib.Path`
    '''
    _set_up_logging()

    if 'drupal_to_solr_script' not in config:
        _log.error('Did not find "drupal_to_solr_script" path in configuration file.')
        raise SystemExit(1)
    else:
        conversion_script_path = pathlib.Path(config['drupal_to_solr_script'])
        try:
            # ensure absolute path
            conversion_script_path = conversion_script_path.resolve()
        except (RuntimeError, FileNotFoundError):
            # this will trigger the SystemExit in the next suite
            conversion_script_path = False

        if not conversion_script_path or not (conversion_script_path.exists() and conversion_script_path.is_file()):
            _log.error('Configuration file\'s path to "drupal_to_solr_script" seems wrong.\nNOT UPDATING ANYTHING.')
            raise SystemExit(1)

    return conversion_script_path


def should_update_this(resource_type, config):
    '''
    Determine whether an update of ``resource_type`` is required, according to the configuration
    given in ``config``.

    :param str resource_type: The resource type to check.
    :param dict config: Dictionary of the configuration file that has our data.
    :returns: Whether the resource type should be updated.
    :rtype: bool
    :raises: :exc:`KeyError` if data for ``resource_type`` is not found in ``config``.
    '''

    _set_up_logging()

    if (resource_type not in config['update_frequency'] or
        resource_type not in config['last_updated']):
        _log.warning('should_update_this(): missing data in config file for {}'.format(resource_type))
        raise KeyError('missing data in config file')

    last_update = datetime.datetime.fromtimestamp(float(config['last_updated'][resource_type]),
                                                  datetime.timezone.utc)
    late_update_delta = _now_wrapper() - last_update

    upd_req_delta = config['update_frequency'][resource_type]
    if upd_req_delta.endswith('d'):
        upd_req_delta = datetime.timedelta(days=int(upd_req_delta[:-1]))
    else:
        upd_req_delta = datetime.timedelta(hours=int(upd_req_delta[:-1]))

    if late_update_delta >= upd_req_delta:
        _log.info('should_update_this(): should update {}'.format(resource_type))
        return True
    else:
        _log.info('should_update_this(): should not update {}'.format(resource_type))
        return False


def calculate_chant_updates(config):
    '''
    Determine which dates should be requested for updates of "chant" resources. This returns a list
    of strings that can be appended to the Drupal URL.

    To ensure no updates are missed, this function always asks for an update for one more day back
    in time than the most recent update. This helps deal with the fact that we don't know which
    timezone the server is using to server our updates.

    :param dict config: Dictionary of the configuration file that has our data.
    :returns: A list of the dates, formatted as YYYYMMDD, that require an update.
    :rtype: list of str

    .. note:: If the last update is in the future, the function returns an empty list.
    '''

    _set_up_logging()

    post = []

    last_update = config['last_updated']['chant']
    last_update = datetime.datetime.fromtimestamp(float(last_update), datetime.timezone.utc)
    delta = _now_wrapper() - last_update

    if delta.total_seconds() < 0:
        # ... last updated in the future?!
        _log.warning('Most recent chant update is in the future? ({})'.format(last_update.strftime('%Y/%m/%d %H:%M')))
    else:
        days_to_request = delta.days + 2
        one_day = datetime.timedelta(days=1)
        cursor = _now_wrapper()
        for _ in range(days_to_request):
            post.append(cursor.strftime('%Y%m%d'))
            cursor -= one_day

    _log.info('Requesting chant updates for {}'.format(post))
    return post


def download_update(resource_type, config):
    '''
    Download the data for the indicated resource type, according to the URL stored in "config." When
    the server has a problem, this function logs the error and returns an empty list.

    :param str resource_type: The resource type for which to fetch updates.
    :param dict config: Dictionary of the configuration file that has our data.
    :returns: The data returned by the Cantus Drupal server---a list of strings with XML documents.
    :rtype: list of str

    .. note:: The return type is a list of strings, not a single string. Some resource types (chant)
        may require updates for multiple days, which will produce multiple XML documents.
    '''

    _set_up_logging()
    _log.info('Will download an update for {}'.format(resource_type))

    client = httpclient.HTTPClient()
    update_url = config['drupal_urls'][resource_type].format(drupal_url=config['drupal_urls']['drupal_url'])

    if 'chant' == resource_type:
        update_urls = ['{}/{}'.format(update_url, x) for x in calculate_chant_updates(config)]
    else:
        update_urls = [update_url]

    try:
        post = []
        for url in update_urls:
            _log.debug('Downloading {} update from {}'.format(resource_type, url))
            response = client.fetch(url)
            post.append(response.body)
        return post
    except (httpclient.HTTPError, IOError) as err:
        _log.warning('Failed to download update for {} ({})'.format(resource_type, err))
        return ['']
    finally:
        client.close()


def convert_update(temp_directory, conversion_script_path, update):
    '''
    Convert a Drupal XML document into a Solr XML document. The Drupal XML document is supplied to
    this function as a string, outputted to the temporary directory, and the conversion script is
    called. The pathname of the converted file is returned.

    :param str temp_directory: The pathname of a (temporary) directory into which the XML documents
        should be saved.
    :param str conversion_script_path: The pathname to the "drupal_xml_to_solr_xml.py" script.
    :param str update: The Drupal XML document that should be converted. This is *not* the path to
        the already-outputted document!
    :returns: The pathname to the file expected as output from the conversion script.
    :rtype: str
    :raises: :exc:`RuntimeError` if the conversion failed for any reason. This function will write
        appropriate log entries.
    '''

    _set_up_logging()

    # calculate filenames
    drupal_xml_filename = '{}/{}'.format(temp_directory, _now_wrapper().strftime('%Y%m%d%H%M%S%f'))
    solr_xml_filename = '{}-out.xml'.format(drupal_xml_filename)
    drupal_xml_filename = '{}.xml'.format(drupal_xml_filename)
    _log.debug('Saving a Drupal XML file to {}'.format(drupal_xml_filename))
    _log.debug('Expecting a Solr XML file at {}'.format(solr_xml_filename))

    # output the Drupal XML file
    with open(drupal_xml_filename, 'wb') as the_file:
        written = the_file.write(update)
    if written < len(update):
        err_msg = 'Could not write Drupal XML file to {}'.format(drupal_xml_filename)
        _log.error(err_msg)
        raise RuntimeError(err_msg)

    # run the conversion script
    try:
        subprocess.check_output([conversion_script_path, drupal_xml_filename])
    except subprocess.CalledProcessError as cperr:
        err_msg = 'Conversion to Solr XML failed ({})'.format(cperr)
        _log.error(err_msg)
        raise RuntimeError(err_msg)

    # double check the Solr XML file exists
    solr_xml_path = pathlib.Path(solr_xml_filename)
    if not solr_xml_path.exists():
        err_msg = 'Conversion script succeeded but Solr XML file is missing at {}'.format(solr_xml_filename)
        _log.error(err_msg)
        raise RuntimeError(err_msg)

    return str(solr_xml_path)


def submit_update(update_pathname, solr_url):
    '''
    Submit a Solr XML file as an update to the Solr server.

    :param str update_pathname: The pathname to a file that holds a Solr XML document that should
        be loaded and submitted to the Solr server.
    :param str solr_url: The full URL to the Solr server, including protocol and port, plus the
        collection name. For example, ``'http://localhost:8983/solr/collection1'``.
    :returns: ``None``
    :raises: :exc:`RuntimeError` if the update file could not be loaded for any reason.
    '''

    _set_up_logging()
    _log.info('Will submit an update to the Solr server at {}'.format(solr_url))

    with open(update_pathname, 'r') as the_file:
        update = the_file.read()

    if solr_url.endswith('/'):
        solr_url = solr_url[:-1]
    update_url = '{}/update?commit=true'.format(solr_url)
    _log.debug('Final Solr URL is {}'.format(update_url))

    client = httpclient.HTTPClient()

    try:
        client.fetch(update_url, method='POST', body=update, headers={'Content-Type': 'application/xml'})
    except (httpclient.HTTPError, IOError) as err:
        err_msg = 'Failed to upload to Solr ({})'.format(err)
        _log.error(err_msg)
        raise RuntimeError(err_msg)
    finally:
        client.close()


def _set_up_logging():
    '''
    Set up logging for the script. This function does not replace the gloabl ``_log`` object if it
    has already been created, so it is safe to run this function many times.
    '''
    global _log
    if _log is None:
        _log = logging.getLogger('holy_orders')
        _log.setLevel(LOG_LEVEL)
        hand = logging.StreamHandler()
        hand.setLevel(LOG_LEVEL)
        hand.setFormatter(logging.Formatter('%(asctime)s (%(name)s) %(levelname)s: %(message)s'))
        _log.addHandler(hand)
        # TODO: enable journald logging when ready
        # _log.addHandler(journalctl.JournalHandler(SYSLOG_IDENTIFIER='holy_orders'))


if '__main__' == __name__ :
    _set_up_logging()
    _log.info('HolyOrders awakens.')

    try:
        config_path = argv[1]
    except IndexError:
        config_path = ''

    main(config_path)
