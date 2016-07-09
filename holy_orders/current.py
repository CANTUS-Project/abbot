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

# settings
LOG_LEVEL = logging.DEBUG

# script-level "globals"
_log = tornado.log.app_log


def _now_wrapper():
    '''
    A wrapper function for datetime.datetime.utcnow() that can be mocked for automated tests.
    '''
    return datetime.datetime.now(datetime.timezone.utc)


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


# TODO: this function is untested
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
