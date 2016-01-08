#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbot/__main__.py
# Purpose:                Main file for the Abbot server.
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
Main file for the Abbot server reference implementation of the Cantus API.
'''

import logging

from tornado import log, ioloop, web
from tornado.options import define, options
from tornado.options import Error as OptionsError

from systemdream.journal import handler as journalctl

import abbot
from abbot.handlers import CanonicalHandler, RootHandler, EverythingElseHandler
from abbot.simple_handler import SimpleHandler
from abbot.complex_handler import ComplexHandler
from abbot.systemd_http_server import SystemdHTTPServer

define('port', default=8888, type=int,
       help='port for Abbot to listen on, between 1024 and 32768')
define('hostname', default='localhost', type=str, help='hostname for FQDN in "resources" links')
define('scheme', default='http', type=str, help='http or https')
define('server_name', default='', type=str, help='automatically set with scheme, hostname, and port; no need to override')


# NOTE: these URLs require a terminating /
HANDLERS = [
    web.url(r'/', RootHandler),
    web.URLSpec(r'.*(?<!/)', CanonicalHandler),  # match anything not ending with a /
    web.URLSpec(r'/browse/', handler=ComplexHandler, name='browse_all',
                kwargs={'type_name': '*',
                        'additional_fields': ['incipit', 'folio', 'position', 'sequence', 'mode',
                                              'id', 'cantus_id', 'full_text_simssa', 'full_text',
                                              'full_text_manuscript', 'volpiano', 'notes',
                                              'cao_concordances', 'melody_id', 'marginalia',
                                              'differentia', 'finalis', 'siglum', 'feast_id',
                                              'genre_id', 'office_id', 'source_id', 'date',
                                              'feast_code', 'mass_or_office', 'display_name',
                                              'given_name', 'family_name', 'institution', 'city',
                                              'country', 'title', 'rism', 'provenance_id',
                                              'century_id', 'notation_style_id', 'segment_id',
                                              'source_status_id', 'summary', 'liturgical_occasions',
                                              'description', 'indexing_notes', 'indexing_date',
                                              'indexers', 'editors', 'proofreaders',
                                              'provenance_detail']}),
    web.URLSpec(r'/centuries/(.*/)?', handler=SimpleHandler, name='view_centuries',
                kwargs={'type_name': 'century'}),
    web.URLSpec(r'/chants/(.*/)?', handler=ComplexHandler, name='view_chants',
                kwargs={'type_name': 'chant',
                        'additional_fields': {'incipit', 'folio', 'position', 'sequence', 'mode',
                                              'id', 'cantus_id', 'full_text_simssa', 'full_text',
                                              'full_text_manuscript', 'volpiano', 'notes',
                                              'cao_concordances', 'melody_id', 'marginalia',
                                              'differentia', 'finalis', 'siglum', 'feast_id',
                                              'genre_id', 'office_id', 'source_id'}}),
    web.URLSpec(r'/feasts/(.*/)?', handler=SimpleHandler, name='view_feasts',
                kwargs={'type_name': 'feast', 'additional_fields': ['date', 'feast_code']}),
    web.URLSpec(r'/genres/(.*/)?', handler=SimpleHandler, name='view_genres',
                kwargs={'type_name': 'genre', 'additional_fields': ['mass_or_office']}),
    web.URLSpec(r'/indexers/(.*/)?', handler=SimpleHandler, name='view_indexers',
                kwargs={'type_name': 'indexer',
                        'additional_fields': ['display_name', 'given_name', 'family_name',
                                              'institution', 'city', 'country']}),
    web.URLSpec(r'/notations/(.*/)?', handler=SimpleHandler, name='view_notations',
                kwargs={'type_name': 'notation'}),
    web.URLSpec(r'/offices/(.*/)?', handler=SimpleHandler, name='view_offices',
                kwargs={'type_name': 'office'}),
    web.URLSpec(r'/portfolia/(.*/)?', handler=SimpleHandler, name='view_portfolia',
                kwargs={'type_name': 'portfolio'}),
    web.URLSpec(r'/provenances/(.*/)?', handler=SimpleHandler, name='view_provenances',
                kwargs={'type_name': 'provenance'}),
    web.URLSpec(r'/sigla/(.*/)?', handler=SimpleHandler, name='view_sigla',
                kwargs={'type_name': 'siglum'}),
    web.URLSpec(r'/segments/(.*/)?', handler=SimpleHandler, name='view_segments',
                kwargs={'type_name': 'segment'}),
    web.URLSpec(r'/sources/(.*/)?', handler=ComplexHandler, name='view_sources',
                kwargs={'type_name': 'source',
                        'additional_fields': ['title', 'rism', 'siglum', 'provenance_id',
                                              'date', 'century_id', 'notation_style_id',
                                              'segment_id', 'source_status_id', 'summary',
                                              'liturgical_occasions', 'description',
                                              'indexing_notes', 'indexing_date', 'indexers',
                                              'editors', 'proofreaders', 'provenance_detail']}),
    web.URLSpec(r'/statii/(.*/)?', handler=SimpleHandler, name='view_source_statii',
                kwargs={'type_name': 'source_status'}),
    web.URLSpec(r'.*', EverythingElseHandler),  # match anything not elsewhere matched
    ]


# TODO: too many branches
# TODO: too many statements
def main():
    '''
    This function creates a Tornado Web Application listening on the specified port, then starts
    an event loop and blocks until the event loop finishes.
    '''

    # Job #1: logging. It's not "quality," contrary to what Ford says.
    logging.root.addHandler(journalctl.JournalHandler(SYSLOG_IDENTIFIER='abbot'))

    # parse commandline options
    try:
        options.parse_command_line(final=False)
    except OptionsError as opt_err:
        print(str(opt_err))
        raise SystemExit(1)

    # see if there's a configuration file for us
    if len(options.options_file) > 1:
        try:
            options.parse_config_file(options.options_file, final=True)
        except FileNotFoundError:
            print('Could not find the options file "{}"\nQuitting.'.format(options.options_file))
            return

    # to allow --copyright, --license, and --licence to work identically
    if options.license or options.copyright:
        options.licence = True

    # print the standard header
    starting_msg = 'Abbot Server {server} for Cantus API {api} is starting up!'.format(
        server=abbot.__version__,
        api=abbot.__cantus_version__)
    log.app_log.warning(starting_msg)
    if options.debug or options.about or options.licence or options.version:
        print(starting_msg)

    # simple, early-end options
    if options.about:
        # thing about Abbot
        print('\nAbbot is a server implementation of the Cantus API, allowing access to a\n'
              'database of Mediaeval chant manuscripts (hand-written books with religious\n'
              'music). You can learn more about the CANTUS Project, which is responsible for\n'
              'Abbot, the Cantus API, and the Cantus Database, at http://cantusdatabase.org/.')
    if options.licence or options.about:
        # thing about the licence
        print('\nAbbot Copyright (C) 2015 Christopher Antila\n'
              'This program comes with ABSOLUTELY NO WARRANTY\n'
              'This is free software, and you are welcome to redistribute it under\n'
              'certaion conditions (Affero General Public Licence, version 3 or later).\n'
              'For details, refer to the LICENSE file or https://gnu.org/licenses/agpl-3.0.html\n'
              'Although the source code is included with Abbot, you may access our source code\n'
              'repository at https://github.com/CANTUS-Project/abbot/\n')
    if options.about or options.licence or options.version:
        return

    # Job #1.5: because Tornado doesn't seem to do its job, we need to set the logging level
    log_level = str(options.logging).lower()
    if log_level == 'debug':
        log.access_log.setLevel(logging.DEBUG)
        log.app_log.setLevel(logging.DEBUG)
        log.gen_log.setLevel(logging.DEBUG)
    elif log_level == 'info':
        log.access_log.setLevel(logging.INFO)
        log.app_log.setLevel(logging.INFO)
        log.gen_log.setLevel(logging.INFO)
    else:
        log.access_log.setLevel(logging.WARN)
        log.app_log.setLevel(logging.WARN)
        log.gen_log.setLevel(logging.WARN)

    # check port is okay
    if not isinstance(options.port, int) or options.port < 1024 or options.port > 32768:
        print('Invalid port ({}). Choose a port between 1024 and 32768.\nExiting.'.format(options.port))
        return

    # check URL access scheme
    if options.scheme.lower() not in ('http', 'https'):
        print('Invalid access scheme ({}). Require "http" or "https"'.format(options.scheme))
        return

    # set the server_name option
    options.server_name = '{scheme}://{hostname}:{port}/'.format(
        scheme=options.scheme,
        hostname=options.hostname,
        port=options.port)

    if options.debug:
        print('Listening on {}'.format(options.server_name))

    # prepare settings for the HTTPServer
    settings = {'debug': options.debug,
                'compress_response': not options.debug,
               }

    server = SystemdHTTPServer(web.Application(handlers=HANDLERS, settings=settings))
    server.listen(options.port)

    if options.debug:
        print('')

    try:
        ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        raise SystemExit(0)


if __name__ == '__main__':
    main()
