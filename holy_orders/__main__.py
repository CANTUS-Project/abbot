#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           holy_orders
# Program Description:    Update program for the Abbot Cantus API server.
#
# Filename:               holy_orders/__main__.py
# Purpose:                Main file for Holy Orders.
#
# Copyright (C) 2015, 2016 Christopher Antila
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
import hashlib
import json
import logging
import os.path
import pathlib
from sys import argv
import tempfile
import time as time_module
from xml.etree import ElementTree as etree

from tornado import httpclient
import tornado.log
from systemdream.journal import handler as journalctl

from holy_orders import configuration
from holy_orders import current
from holy_orders import drupal_to_solr

# settings
LOG_LEVEL = logging.DEBUG

# script-level "globals"
_log = tornado.log.app_log


def _now_wrapper():
    '''
    A wrapper function for datetime.datetime.utcnow() that can be mocked for automated tests.
    '''
    return datetime.datetime.now(datetime.timezone.utc)


def main(config_path):
    '''
    Run Holy Orders.

    :param str config_path: Pathname to the HolyOrders configuration file.
    '''

    config, updates_db = configuration.load_db(configuration.verify(configuration.load(config_path)))

    for rtype in config['general']['resource_types'].split(','):
        try:
            if current.should_update(rtype, config, updates_db):
                update_time = _now_wrapper()
                list_of_updates = download_update(rtype, config)

                if list_of_updates:
                    update_worked = process_and_submit_updates(list_of_updates, config)
                    if update_worked:
                        current.update_db(updates_db, rtype, update_time)
                    else:
                        _log.error('Conversion and submission failed for {0}'.format(rtype))

                else:
                    _log.error('Failed to download {0} updates from Drupal'.format(rtype))

        except Exception as exc:
            _log.error('Unexpected error in main(): "{0}: {1}"'.format(type(exc), exc))

    commit_then_optimize(config['general']['solr_url'])


def process_and_submit_updates(updates, config):
    '''
    Given a list of updates from Drupal, convert the documents to Solr XML and submit them to Solr.

    :param updates: The updates from Drupal.
    :type updates: list of str
    :param dict config: Dictionary of the configuration file that has our data.
    :returns: Whether all the updates were successfully converted and submitted.
    :rtype: bool
    '''

    updates_have_failed = False
    converted = []
    for update in updates:
        try:
            converted.append(drupal_to_solr.convert(update))
        except Exception as exc:
            updates_have_failed = True

    for i, update in enumerate(converted):
        if i != 0 and i % 100 == 0:
            time_module.sleep(5)
        try:
            submit_update(update, config['general']['solr_url'])
        except RuntimeError:
            updates_have_failed = True

    if updates_have_failed:
        _log.error('At least one update has failed during conversion and submission.')

    return not updates_have_failed


def download_from_urls(url_list):
    '''
    Given a list of URLs, do a GET request on each and return the response bodies.

    :parm url_list: The URLs from which to download.
    :type url_list: list of str
    :returns: The response bodies from the specified URLs, in the order specified.
    :rtype: list of str

    If one of the requests fails, a "warning" log message is emitted, and the function returns an
    empty list.

    Resposne bodies are converted from bytes to str objects, and we assume it is UTF-8 encoded.
    '''

    _log.debug('now in download_from_urls()')

    try:
        post = []
        client = httpclient.HTTPClient()
        for url in url_list:
            _log.debug('download_from_urls() is downloading {}'.format(url))
            response = client.fetch(url)
            post.append(str(response.body, 'UTF-8'))
        return post
    except (httpclient.HTTPError, IOError, ValueError) as err:
        _log.warning('download_from_urls() failed to download update from {}'.format(err))
        return []
    finally:
        client.close()


def _collect_chant_ids(daily_updates):
    '''
    Used by download_chant_updates().

    From a list of XML documents that contain the chant IDs updated on a particular day,
    collect all the IDs.

    :param daily_updates: The XML documents with the chant IDs that were updated (see below).
    :type daily_updates: list of str or bytestr that contain an XML document
    :returns: A list of the chant IDs that must be downloaded.
    :rtype: list of str

    **Format of Daily Updates**

    The "daily_updates" parameter is a list of str or bytes objects. Each must contain an XML
    document that has a list of chant IDs. The document will look something like this:

    <chants>
        <chant>
            <id>123456</id>
        </chant>
        <chant>
            <id>720922</id>
        </chant>
    </chants>
    '''

    _log.debug('Now in _collect_chant_ids()')

    if isinstance(daily_updates, bytes):
        try:
            daily_updates = str(daily_updates, 'UTF-8')
        except UnicodeDecodeError:
            _log.error('_collect_chant_ids() failed to convert input to str')
            return []

    post = {}
    for each_day in daily_updates:
        try:
            each_day = etree.fromstring(each_day)
        except etree.ParseError:
            _log.error('_collect_chant_ids() received invalid XML')
            return []

        for elem in each_day.iter('id'):
            post[elem.text] = None

    return list(post.keys())


def download_chant_updates(config):
    '''
    Download required data for updating chant resources.

    :param config: The configuration file that has our data.
    :type config: :class:`configparser.ConfigParser`
    :returns: The data returned by the Cantus Drupal server---a list of strings with XML documents.
    :rtype: list of str

    The update download process for chants is much more complicated than other resource types. To
    avoid complications with Drupal, the server first returns a document with the ID of chants that
    were updated on a particular day. Then we have to request each chant separately. This avoids
    the situation where so many chants are updated in a single day that Drupal would "time-out" the
    request before it finishes formatting all the results.

    In case Drupal still fails, this function writes an ERROR log message about the failure for
    that day, and returns an empty list so that the "last updated" date will not change.
    '''

    _log.info('Starting download_chant_updates()')

    # get the lists of chant IDs that were updated, by day
    base_url = config['drupal_urls']['chants_updated']
    if '{date}' not in base_url:
        # this turns out to be a serious problem, when the URLs are improperly formatted
        _log.error('Cannot download chants: improper "chants_updated" URL')
        return []
    update_urls = [base_url.format(date=x) for x in current.calculate_chant_updates(config)]
    ids_lists = download_from_urls(update_urls)

    # pull out the IDs of all the chants we need to download
    chant_ids = _collect_chant_ids(ids_lists)

    # download all the chants by ID
    chant_url = config['drupal_urls']['chant_id']
    if '{id}' not in chant_url:
        # this turns out to be a serious problem, when the URLs are improperly formatted
        _log.error('Cannot download chants: improper "chant_id" URL')
        return []
    update_urls = [chant_url.format(id=each_id) for each_id in chant_ids]
    return download_from_urls(update_urls)


def download_update(resource_type, config):
    '''
    Download the data for the indicated resource type, according to the URL stored in "config."

    :param str resource_type: The resource type for which to fetch updates.
    :param config: The configuration file that has our data.
    :type config: :class:`configparser.ConfigParser`
    :returns: The data returned by the Cantus Drupal server---a list of strings with XML documents.
    :rtype: list of str

    .. note:: The return type is always a *list* of bytestrings, not a single one. Some resource
        types (chants) may require multiple XML documents for the update.
    '''

    if 'chant' == resource_type:
        return download_chant_updates(config)

    _log.info('Starting download_update() for {}'.format(resource_type))

    return download_from_urls([config['drupal_urls'][resource_type]])


def submit_update(update, solr_url):
    '''
    Submit a Solr XML file as an update to the Solr server.

    :param update: A Solr XML document to submit to the Solr server.
    :type update: :class:`xml.etree.ElementTree.Element`
    :param str solr_url: The full URL to the Solr server, including protocol and port, plus the
        collection name. For example, ``'http://localhost:8983/solr/collection1'``.
    :returns: ``None``
    :raises: :exc:`RuntimeError` if the update file could not be loaded for any reason.
    '''

    _log.info('Will submit an update to the Solr server at {}'.format(solr_url))

    update = etree.tostring(update, encoding='unicode')

    if solr_url.endswith('/'):
        solr_url = solr_url[:-1]
    update_url = '{}/update?commit=false'.format(solr_url)
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


def commit_then_optimize(solr_url):
    '''
    Given the URL to a Solr installation, ask it to commit then optimize the most recent updates.

    :param str solr_url: The full URL to the Solr server, including protocol and port, plus the
        collection name. For example, ``'http://localhost:8983/solr/collection1'``.
    :returns: 0 if everything was successful; 1 if the commit failed; 2 if the optimize failed.
    :rtype: int
    '''

    while solr_url.endswith('/'):
        solr_url = solr_url[:-1]

    commit_url = '{}/update?commit=true'.format(solr_url)
    optimize_url = '{}/update?optimize=true'.format(solr_url)

    # We'll wait five minutes for each step to complete. It's a long time, but there's no rush.
    request_timeout = 5 * 60

    client = httpclient.HTTPClient()

    try:
        try:
            _log.info('Asking Solr to "commit" the updates.')
            client.fetch(commit_url, method='GET', request_timeout=request_timeout)
        except (httpclient.HTTPError, IOError) as err:
            err_msg = 'Solr failed during the "commit" ({})'.format(err)
            _log.error(err_msg)
            return 1

        try:
            _log.info('Asking Solr to "optimize" the updates.')
            client.fetch(optimize_url, method='GET', request_timeout=request_timeout)
        except (httpclient.HTTPError, IOError) as err:
            err_msg = 'Solr failed during the "optimize" ({})'.format(err)
            _log.error(err_msg)
            return 2

    finally:
        client.close()

    return 0


if '__main__' == __name__ :
    logging.root.addHandler(journalctl.JournalHandler(SYSLOG_IDENTIFIER='holy_orders'))
    _log.setLevel(LOG_LEVEL)
    _log.info('HolyOrders awakens.')

    try:
        config_path = argv[1]
    except IndexError:
        config_path = ''

    main(config_path)
