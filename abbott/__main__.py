#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/__main__.py
# Purpose:                Manage startup and shutdown of the program.
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

# NOTE: this is just a sketch for now!

from tornado import ioloop, web, httpclient, gen, escape
import pysolrtornado

SOLR =  pysolrtornado.Solr('http://localhost:8983/solr/', timeout=10)


@gen.coroutine
def ask_solr_by_id(q_type, q_id):
    '''
    Query the Solr server for a record of "q_type" and an id of "q_id."

    This function uses the "pysolrtornado" library.
    '''
    return (yield SOLR.search('+type:{} +id:{}'.format(q_type, q_id)))


class ChantHandler(web.RequestHandler):
    '''
    '''
    # List of all fields we should try to provide:
    # incipit, source, marginalia, folio, sequence, office, genre, position, cantus_id, feast,
    # feast_desc, mode, differentia, finalis, full_text, full_text_manuscript, full_text_simssa,
    # volpiano, notes, cao_concordances, siglum, proofreader, cantus_id, melody_id

    @staticmethod
    @gen.coroutine
    def format_chant(chant):
        '''
        Given a dict with a Solr response for a Chant record, convert the fields ending with "_id"
        into the appropriate "name" or "title" of the corresponding resource.
        '''
        # NOTE: 'siglum' is a taxonomy term in Source but text field in Chant
        DIRECT_INCLUDE = ['incipit', 'folio', 'position', 'sequence', 'mode', 'id', 'cantus_id',
                          'full_text_simssa', 'full_text_manuscript', 'volpiano', 'notes',
                          'cao_concordances', 'melody_id', 'marginalia', 'differentia', 'finalis',
                          'siglum']
        LOOKUP = {'feast_id': ('feast', 'feast'),
                  'genre_id': ('genre', 'genre'),
                  'office_id': ('office', 'office'),
                  }  # value[0] is the "q_type" to lookup; value[1] is what it's called in "formatted"

        formatted = {}

        for key in iter(chant):
            if key in DIRECT_INCLUDE:
                formatted[key] = chant[key]
            elif key in LOOKUP:
                resp = yield ask_solr_by_id(LOOKUP[key][0], chant[key])
                if len(resp) > 0:
                    formatted[LOOKUP[key][1]] = resp[0]['name']
            elif key == 'source_id':
                resp = yield ask_solr_by_id('source', chant[key])
                if len(resp) > 0:
                    formatted['source'] = resp[0]['title']

        # fetch extra information
        if 'feast_id' in chant:  # for "feast_desc"
            #results = yield ask_solr_by_id('feast', chant['feast_id'])
            #for feast in results:
                #formatted['feast_desc'] = feast['description']
            resp = yield ask_solr_by_id('feast', chant['feast_id'])
            if len(resp) > 0:
                formatted['fest_desc'] = resp[0]['description']

        if 'cantus_id' in chant:  # for "full_text"
            resp = yield ask_solr_by_id('cantusid', chant['cantus_id'])
            if len(resp) > 0 and 'full_text' in resp[0]:
                formatted['full_text'] = resp[0]['full_text']

        # TODO: implement the proofreader parts; they seem always empty in Drupal...

        return formatted

    @gen.coroutine
    def get(self, chant_id=None):
        # adjust for missing or malformed chant_id
        if chant_id is None:
            chant_id = '*'
        elif chant_id.endswith('/') and len(chant_id) > 1:
            chant_id = chant_id[:-1]

        # query Solr and format our response body
        resp = yield ask_solr_by_id('chant', chant_id)
        if len(resp) > 0:
            post = ''
            for chant in resp:
                post += str((yield self.format_chant(chant))) + '\n\n'
        else:
            post = '[]\n\n'

        # prepare the rest of the response
        self.write(post)


class FeastHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, feast_id=None):
        if feast_id:
            if feast_id.endswith('/') and len(feast_id) > 1:
                feast_id = feast_id[:-1]
            post = yield ask_solr_by_id('feast', feast_id)
            if 0 == len(post):
                post = 'feast {} not found\n'.format(feast_id)
            else:
                soup = ''
                for each in post:
                    soup += str(each) + '\n\n'
                post = soup
        else:
            post = 'generic info about feasts\n'
        self.write(post)


class RootHandler(web.RequestHandler):
    def get(self):
        post = 'Abbott\n======\n'
        post += '-> browse_chants: {}\n'.format(self.reverse_url('browse_chants', 'id'))
        post += '-> browse_feasts: {}\n'.format(self.reverse_url('browse_feasts', 'id'))
        post += '\n'
        self.write(post)


def make_app():
    '''
    NOTE: these URLs require a terminating /
    '''
    return web.Application([
        web.url(r'/', RootHandler),
        web.url(r'/chants/(.*/)?', ChantHandler, name='browse_chants'),
        web.url(r'/feasts/(.*/)?', FeastHandler, name='browse_feasts'),
        ])


def main():
    app = make_app()
    app.listen(8888)
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
