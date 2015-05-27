#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/__main__.py
# Purpose:                Main file for the Abbott server.
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
Main file for the Abbott server reference implementation of the Cantus API.
'''

from tornado import ioloop, web
from abbott import handlers

PORT = 8888


# NOTE: these URLs require a terminating /
HANDLERS = [
    web.url(r'/', handlers.RootHandler),
    web.URLSpec(r'/cantusids/(.*/)?', handler=handlers.ComplexHandler, name='browse_cantusids',
                kwargs={'type_name': 'cantusid',
                        'additional_fields': ['incipit', 'full_text', 'genre_id']}),
    web.URLSpec(r'/centuries/(.*/)?', handler=handlers.SimpleHandler, name='browse_centuries',
                kwargs={'type_name': 'century'}),
    web.URLSpec(r'/chants/(.*/)?', handler=handlers.ComplexHandler, name='browse_chants',
                kwargs={'type_name': 'chant',
                        'additional_fields': {'incipit', 'folio', 'position', 'sequence', 'mode',
                                              'id', 'cantus_id', 'full_text_simssa', 'full_text',
                                              'full_text_manuscript', 'volpiano', 'notes',
                                              'cao_concordances', 'melody_id', 'marginalia',
                                              'differentia', 'finalis', 'siglum', 'feast_id',
                                              'genre_id', 'office_id', 'source_id'}}),
    web.URLSpec(r'/feasts/(.*/)?', handler=handlers.SimpleHandler, name='browse_feasts',
                kwargs={'type_name': 'feast', 'additional_fields': ['date', 'feast_code']}),
    web.URLSpec(r'/genres/(.*/)?', handler=handlers.SimpleHandler, name='browse_genres',
                kwargs={'type_name': 'genre', 'additional_fields': ['mass_or_office']}),
    web.URLSpec(r'/indexers/(.*/)?', handler=handlers.ComplexHandler, name='browse_indexers',
                kwargs={'type_name': 'indexer',
                        'additional_fields': ['display_name', 'given_name', 'family_name',
                                              'institution', 'city', 'country']}),
    web.URLSpec(r'/notations/(.*/)?', handler=handlers.SimpleHandler, name='browse_notations',
                kwargs={'type_name': 'notation'}),
    web.URLSpec(r'/offices/(.*/)?', handler=handlers.SimpleHandler, name='browse_offices',
                kwargs={'type_name': 'office'}),
    web.URLSpec(r'/portfolia/(.*/)?', handler=handlers.SimpleHandler, name='browse_portfolia',
                kwargs={'type_name': 'portfolio'}),
    web.URLSpec(r'/provenances/(.*/)?', handler=handlers.SimpleHandler, name='browse_provenances',
                kwargs={'type_name': 'provenance'}),
    web.URLSpec(r'/sigla/(.*/)?', handler=handlers.SimpleHandler, name='browse_sigla',
                kwargs={'type_name': 'siglum'}),
    web.URLSpec(r'/segments/(.*/)?', handler=handlers.SimpleHandler, name='browse_segments',
                kwargs={'type_name': 'segment'}),
    web.URLSpec(r'/sources/(.*/)?', handler=handlers.ComplexHandler, name='browse_sources',
                kwargs={'type_name': 'source',
                        'additional_fields': ['title', 'rism', 'siglum', 'provenance_id',
                                              'date', 'century_id', 'notation_style_id',
                                              'segment_id', 'source_status_id', 'summary',
                                              'liturgical_occasions', 'description',
                                              'indexing_notes', 'indexing_date', 'indexers',
                                              'editors', 'proofreaders', 'provenance_detail']}),
    web.URLSpec(r'/statii/(.*/)?', handler=handlers.SimpleHandler, name='browse_source_statii',
                kwargs={'type_name': 'source_status'}),
    ]


def main(port=None):
    '''
    This function creates a Tornado Web Application listening on the specified port, then starts
    an event loop and blocks until the event loop finishes.

    :param int port: The optional port to listen on. If not provided, we will try to start on the
        module-level ``PORT`` value after checking its validity (an integer between 1024 and 32768
        exclusive). If ``PORT`` is invalid, the server will start on port 8888.
    '''

    if port is None:
        if isinstance(PORT, int) and PORT > 1024 and PORT < 32768:
            port = PORT
        else:
            port = 8888

    app = web.Application(HANDLERS)
    app.listen(port)
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
