#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           holy_orders
# Program Description:    Update program for the Abbot Cantus API server.
#
# Filename:               holy_orders/current.py
# Purpose:                Functions to determine which resources to update.
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
Functions to determine which resources to update.
'''

import datetime
import logging

import tornado.log

import iso8601

# settings
LOG_LEVEL = logging.DEBUG

# script-level "globals"
_log = tornado.log.app_log


def _now_wrapper():
    '''
    A wrapper function for datetime.datetime.utcnow() that can be mocked for automated tests.
    '''
    return datetime.datetime.now(datetime.timezone.utc)


def get_last_updated(updates_db, rtype):
    '''
    Get a :class:`datetime` of the most recent update for a resource type.

    :param updates_db: A :class:`Connection` to the database that holds
    :type updates_db: :class:`sqlite3.Connection`
    :param str rtype: The resource type to check.
    :returns: The time of the most recent update for the resource type.
    :rtype: :class:`datetime.datetime`

    If the database's most recent update is recorded as ``'never'``, meaning the resource type was
    never updated, the :class:`datetime` returned corresponds to Unix time ``0``.
    '''
    last_update = updates_db.cursor().execute('SELECT updated FROM rtypes WHERE name=?', (rtype,))
    last_update = last_update.fetchone()[0]
    if last_update == 'never':
        return datetime.datetime.fromtimestamp(0.0)
    else:
        return iso8601.parse_date(last_update)


def should_update(rtype, config, updates_db):
    '''
    Check whether HolyOrders "should update" resources of a particular type.

    :param str rtype: The resource type to check.
    :param config: Dictionary of the configuration file that has our data.
    :type config: :class:`configparser.ConfigParser`
    :param updates_db: A :class:`Connection` to the database that holds
    :type updates_db: :class:`sqlite3.Connection`
    :returns: Whether the resource type should be updated.
    :rtype: bool
    '''

    last_update = get_last_updated(updates_db, rtype)
    if last_update.year < 1990:
        _log.info('should_update({0}) -> True (first update)'.format(rtype))
        return True
    late_update_delta = _now_wrapper() - last_update

    update_freq_delta = config['update_frequency'][rtype]
    if update_freq_delta.endswith('d'):
        update_freq_delta = datetime.timedelta(days=int(update_freq_delta[:-1]))
    else:
        update_freq_delta = datetime.timedelta(hours=int(update_freq_delta[:-1]))

    if late_update_delta >= update_freq_delta:
        _log.info('should_update({0}) -> True'.format(rtype))
        return True
    else:
        _log.info('should_update({0}) -> False'.format(rtype))
        return False


def calculate_chant_updates(updates_db):
    '''
    Determine which dates should be requested for updates of "chant" resources.

    :param updates_db: A :class:`Connection` to the database that holds
    :type updates_db: :class:`sqlite3.Connection`
    :returns: The dates that require an update. These are formatted as YYYYMMD, so they may be used
        directly in Drupal URLs.
    :rtype: list of str

    If no updates are required, the function returns an empty list. To ensure no updates are missed,
    this function always includes one additional day than required. For example, if the most recent
    update was earlier today, then this function requests updates for both today and yesterday.

    However, also note that "days ago" is determined in 24-hour periods, rather than the "yesterday"
    style of thinking that humans use. The actual dates requested aren't especially important---it's
    enough to know that this function errs on the side of requesting more days than required.
    '''

    post = []

    last_update = get_last_updated(updates_db, 'chant')
    delta = _now_wrapper() - last_update

    if delta.total_seconds() >= 0:
        days_to_request = delta.days + 2
        one_day = datetime.timedelta(days=1)
        cursor = _now_wrapper()
        for _ in range(days_to_request):
            post.append(cursor.strftime('%Y%m%d'))
            cursor -= one_day

    _log.info('Requesting chant updates for {}'.format(post))
    return post


def update_db(updates_db, rtype, time):
    '''
    Revise the updates database to show a new "last updated" time for a resource type.

    :param updates_db: A :class:`Connection` to the database that holds
    :type updates_db: :class:`sqlite3.Connection`
    :param str rtype: The resource type that was updated.
    :param time: The time at which the resource type is current.
    :type time: :class:`datetime.datetime`

    While it's tempting to think that the ``time`` argument should correspond to the moment this
    function is called, that's not true---especially for resource types that take considerable time
    to update (chants). Therefore the :class:`datetime` given to this function should correspond
    to the moment just before data are requested from Drupal.
    '''
    time = time.isoformat()
    updates_db.cursor().execute('UPDATE rtypes SET updated=? WHERE name=?;', (time, rtype))
    updates_db.commit()
