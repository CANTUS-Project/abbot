#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/shared.py
# Purpose:                Shared classes and functions for Abbot's automated test suite.
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
Shared classes and functions for Abbot's automated test suite.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock
from tornado import concurrent, testing, web
from tornado.options import options
import pysolrtornado
import abbot
from abbot import __main__ as main

# ensure we have a consistent "server_name" for all the tests
options.server_name = 'https://cantus.org/'


def make_future(with_this):
    '''
    Creates a new :class:`Future` with the function's argument as the result.
    '''
    val = concurrent.Future()
    val.set_result(with_this)
    return val

def make_results(docs):
    '''
    Create a new :class:`pysolrtornado.Results` instance with the ``docs`` argument as the
    :attr:`docs` attribute. This also sets the proper "hits" attribute.

    :param docs: The actual results returned from Solr.
    :type docs: list of dict
    '''
    return pysolrtornado.Results({'response': {'numFound': len(docs), 'docs': docs}})


class TestHandler(testing.AsyncHTTPTestCase):
    "Base class for classes that test a ___Handler."

    def get_app(self):
        return web.Application(main.HANDLERS)

    def check_standard_header(self, on_this):
        '''
        Verify the proper values for the headers that should be part of every response:

        - Server
        - X-Cantus-Version
        - Access-Control-Allow-Headers
        - Access-Control-Expose-Headers
        - Access-Control-Allow-Origin (if the "debug" setting is True)

        :param on_this: The :class:`Response` object to verify.
        :type on_this: :class:`tornado.httpclient.HTTPResponse`
        '''
        exp_server = 'Abbot/{}'.format(abbot.__version__)
        exp_cantus_version = 'Cantus/{}'.format(abbot.__cantus_version__)
        exp_allow_headers = ','.join(abbot.CANTUS_REQUEST_HEADERS)
        exp_expose_headers = ','.join(abbot.CANTUS_RESPONSE_HEADERS)
        exp_allow_origin = self._simple_options.cors_allow_origin

        self.assertEqual(exp_server, on_this.headers['Server'])
        self.assertEqual(exp_cantus_version, on_this.headers['X-Cantus-Version'])
        if self._simple_options.cors_allow_origin:
            self.assertEqual(exp_allow_headers, on_this.headers['Access-Control-Allow-Headers'])
            self.assertEqual(exp_expose_headers, on_this.headers['Access-Control-Expose-Headers'])
            self.assertEqual(exp_allow_origin, on_this.headers['Access-Control-Allow-Origin'])

    def setUp(self):
        '''
        Install a mock on the global "options" modules. The following options are mocked in the
        :mod:`simple_handler` module:

        - drupal_url: None
        - server_name: 'https://cantus.org/'
        - cors_allow_origin: 'https://cantus.org:5733/'
        '''
        super(TestHandler, self).setUp()
        self._simple_options_patcher = mock.patch('abbot.simple_handler.options')
        self._simple_options = self._simple_options_patcher.start()
        self._simple_options.drupal_url = None
        self._simple_options.server_name = 'https://cantus.org/'
        self._simple_options.cors_allow_origin = 'https://cantus.org:5733/'

    def tearDown(self):
        '''
        Remove the mock from the global "options" modules.
        '''
        self._simple_options_patcher.stop()
        super(TestHandler, self).tearDown()
