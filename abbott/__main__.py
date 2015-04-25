#!/usr/bin/env python3
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


class TaxonomyHandler(web.RequestHandler):
    '''
    For the resource types that were a "taxonomy" type in Drupal. They have many fewer fields than
    the other types, so we can have a common base class like this.
    '''

    RETURNED_FIELDS = ['id', 'name', 'description']
    '''
    Names of the fields that TaxonomyHandler will return; others are removed. Subclasses may modify
    these as required.
    '''

    def format_record(self, record):
        post = {}

        for key in iter(record):
            if key in self.RETURNED_FIELDS:
                post[key] = record[key]

        return post

    @gen.coroutine
    def super_get(self, resource_id, type_name, type_name_plural):
        if not resource_id:
            resource_id = '*'
        elif resource_id.endswith('/') and len(resource_id) > 1:
            resource_id = resource_id[:-1]

        resp = yield ask_solr_by_id(type_name, resource_id)

        if 0 == len(resp):
            post = '{} {} not found\n'.format(type_name, resource_id)
        else:
            post = ''
            for each_record in resp:
                post += str(self.format_record(each_record)) + '\n\n'

        return post


class CenturyHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, century_id):
        self.write((yield self.super_get(century_id, 'century', 'centuries')))


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


class FeastHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, feast_id):
        self.write((yield self.super_get(feast_id, 'feast', 'feasts')))


class GenreHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, genre_id):
        self.write((yield self.super_get(genre_id, 'genre', 'genres')))


class NotationHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, notation_id):
        self.write((yield self.super_get(notation_id, 'notation', 'notations')))


class OfficeHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, office_id):
        self.write((yield self.super_get(office_id, 'office', 'offices')))


class PortfolioHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, portfolio_id):
        self.write((yield self.super_get(portfolio_id, 'portfolio', 'portfolia')))


class ProvenanceHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, provenance_id):
        self.write((yield self.super_get(provenance_id, 'provenance', 'provenances')))


class SiglumHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, siglum_id):
        self.write((yield self.super_get(siglum_id, 'siglum', 'sigla')))


class SegmentHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, segment_id):
        self.write((yield self.super_get(segment_id, 'segment', 'segments')))


class SourceStatusHandler(TaxonomyHandler):
    @gen.coroutine
    def get(self, status_id):
        self.write((yield self.super_get(status_id, 'source_status', 'statii')))


class RootHandler(web.RequestHandler):
    def get(self):
        post = ('Abbott\n======\n' +
                #'-> browse_cantusids: {}\n'.format(self.reverse_url('browse_s', 'id')) +
                '-> browse_centuries: {}\n'.format(self.reverse_url('browse_centuries', 'id')) +
                '-> browse_chants: {}\n'.format(self.reverse_url('browse_chants', 'id')) +
                '-> browse_feasts: {}\n'.format(self.reverse_url('browse_feasts', 'id')) +
                '-> browse_genres: {}\n'.format(self.reverse_url('browse_genres', 'id')) +
                #'-> browse_indexers: {}\n'.format(self.reverse_url('browse_s', 'id')) +
                '-> browse_notations: {}\n'.format(self.reverse_url('browse_notations', 'id')) +
                '-> browse_offices: {}\n'.format(self.reverse_url('browse_offices', 'id')) +
                '-> browse_portfolia: {}\n'.format(self.reverse_url('browse_portfolia', 'id')) +
                '-> browse_provenances: {}\n'.format(self.reverse_url('browse_provenances', 'id')) +
                '-> browse_sigla: {}\n'.format(self.reverse_url('browse_sigla', 'id')) +
                '-> browse_segments: {}\n'.format(self.reverse_url('browse_segments', 'id')) +
                #'-> browse_sources: {}\n'.format(self.reverse_url('browse_s', 'id')) +
                '-> browse_source_statii: {}\n'.format(self.reverse_url('browse_source_statii', 'id')) +
                '\n')
        self.write(post)


def make_app():
    '''
    NOTE: these URLs require a terminating /
    '''
    return web.Application([
        web.url(r'/', RootHandler),
        #web.url(r'/cantusids/(.*/)?', CantusidHandler, name='browse_cantusids'),
        web.url(r'/centuries/(.*/)?', CenturyHandler, name='browse_centuries'),
        web.url(r'/chants/(.*/)?', ChantHandler, name='browse_chants'),
        web.url(r'/feasts/(.*/)?', FeastHandler, name='browse_feasts'),
        web.url(r'/genres/(.*/)?', GenreHandler, name='browse_genres'),
        #web.url(r'/indexers/(.*/)?', IndexerHandler, name='browse_indexers'),
        web.url(r'/notations/(.*/)?', NotationHandler, name='browse_notations'),
        web.url(r'/offices/(.*/)?', OfficeHandler, name='browse_offices'),
        web.url(r'/portfolia/(.*/)?', PortfolioHandler, name='browse_portfolia'),
        web.url(r'/provenances/(.*/)?', ProvenanceHandler, name='browse_provenances'),
        web.url(r'/sigla/(.*/)?', SiglumHandler, name='browse_sigla'),
        web.url(r'/segments/(.*/)?', SegmentHandler, name='browse_segments'),
        #web.url(r'/sources/(.*/)?', SourceHandler, name='browse_sources'),
        web.url(r'/statii/(.*/)?', SourceStatusHandler, name='browse_source_statii'),
        ])


def main():
    app = make_app()
    app.listen(8888)
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
