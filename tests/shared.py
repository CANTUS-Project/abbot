#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/shared.py
# Purpose:                Shared classes and functions for Abbott's automated test suite.
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
Shared classes and functions for Abbott's automated test suite.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from tornado import concurrent, testing, web
import pysolrtornado
import abbott
from abbott import __main__ as main


def make_future(with_this):
    '''
    Creates a new :class:`Future` with the function's argument as the result.
    '''
    val = concurrent.Future()
    val.set_result(with_this)
    return val

def make_results(docs):
    '''
    Create a new :class:`pysolrtornado.Results` with the ``docs`` argument as the :attr:`docs`
    attribute.

    :param docs: The actual results returned from Solr.
    :type docs: list of dict
    '''
    return pysolrtornado.Results(docs, len(docs))


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
        - Access-Control-Allow-Origin (if DEBUG is True)

        :param on_this: The :class:`Response` object to verify.
        :type on_this: :class:`tornado.httpclient.HTTPResponse`
        '''
        exp_server = 'Abbott/{}'.format(abbott.__version__)
        exp_cantus_version = 'Cantus/{}'.format(abbott.__cantus_version__)
        exp_allow_headers = ','.join(abbott.CANTUS_REQUEST_HEADERS)
        exp_expose_headers = ','.join(abbott.CANTUS_RESPONSE_HEADERS)
        exp_allow_origin = 'http://localhost:8000'

        self.assertEqual(exp_server, on_this.headers['Server'])
        self.assertEqual(exp_cantus_version, on_this.headers['X-Cantus-Version'])
        self.assertEqual(exp_allow_headers, on_this.headers['Access-Control-Allow-Headers'])
        self.assertEqual(exp_expose_headers, on_this.headers['Access-Control-Expose-Headers'])
        if abbott.DEBUG:
            self.assertEqual(exp_allow_origin, on_this.headers['Access-Control-Allow-Origin'])
