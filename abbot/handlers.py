#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbot/complex_handler.py
# Purpose:                Miscellaneous handlers for the Abbot server.
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
Miscellaneous handlers for the Abbot server.
'''

from tornado import options, web
from abbot.simple_handler import SimpleHandler


class RootHandler(web.RequestHandler):
    '''
    For requests to the root URL (i.e., ``/``).
    '''

    _ALLOWED_METHODS = 'GET, OPTIONS'
    # value of the "Allow" header in response to an OPTIONS request

    def set_default_headers(self):
        '''
        Use :meth:`SimpleHandler.set_default_headers` to set the default headers.
        '''
        SimpleHandler.set_default_headers(self)

    def prepare_get(self):
        '''
        Does the actual work for a GET request at '/'. It's a different method for easier testing.
        '''

        # this ends with a / so we'll have to remove that
        server_name = options.options.server_name[:-1]

        all_plural_resources = [
            'cantusids',
            'centuries',
            'chants',
            'feasts',
            'genres',
            'indexers',
            'notations',
            'offices',
            'portfolia',
            'provenances',
            'sigla',
            'segments',
            'sources',
            'source_statii'
            ]
        post = {'browse': {}, 'view': {}}
        for resource_type in all_plural_resources:
            this_url = '{}{}'.format(server_name,
                                     self.reverse_url('view_{}'.format(resource_type), 'id'))
            post['view'][resource_type] = this_url
            post['browse'][resource_type] = this_url[:-3]
        post['browse']['all'] = '{}{}'.format(server_name, self.reverse_url('browse_all'))
        return {'resources': post}

    def get(self):  # pylint: disable=arguments-differ
        '''
        Handle GET requests to the root URL. Returns a "resources" member with URLs to all available
        search and browse URLs.
        '''
        self.add_header('X-Cantus-Include-Resources', 'true')
        self.write(self.prepare_get())

    def options(self):  # pylint: disable=arguments-differ
        '''
        Response to OPTIONS requests. Sets the "Allow" header and returns.
        '''
        self.add_header('Allow', RootHandler._ALLOWED_METHODS)


class CanonicalHandler(web.RequestHandler):
    '''
    For requests that don't end with a slash, this handler sends a redirect response to the same
    URL with a trailing slash. In other words, this handler ensures user agents are requesting a
    resource's canonical URL (the version with trailing slash).
    '''

    SUPPORTED_METHODS = ('GET', 'HEAD', 'OPTIONS', 'SEARCH')
    # this registers the SEARCH method as something that Tornado can do

    def set_default_headers(self):
        '''
        Use :meth:`SimpleHandler.set_default_headers` to set the default headers.
        '''
        SimpleHandler.set_default_headers(self)

    def _do_the_redirect(self):
        self.redirect('{}/'.format(self.request.uri), permanent=True)

    def get(self):
        self._do_the_redirect()

    def head(self):
        self._do_the_redirect()

    def options(self):
        self._do_the_redirect()

    def search(self):
        self._do_the_redirect()
