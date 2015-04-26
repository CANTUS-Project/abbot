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
'''
'''

# NOTE: this is just a sketch for now!

from tornado import ioloop, web, httpclient, gen, escape
import pysolrtornado

SOLR =  pysolrtornado.Solr('http://localhost:8983/solr/', timeout=10)
DRUPAL_PATH = 'http://cantus2.uwaterloo.ca'
ABBOTT_VERSION = '0.0.1-dev'
CANTUS_API_VERSION = '0.1.0'


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

    returned_fields = ['id', 'name', 'description']
    '''
    Names of the fields that TaxonomyHandler will return; others are removed. Subclasses may modify
    these as required.
    '''

    def initialize(self, type_name, type_name_plural, additional_fields=None):
        '''
        :param additional_fields: Optional list of fields to append to ``self.returned_fields``.
        :type additional_fields: list of str
        '''
        self.type_name = type_name
        self.type_name_plural = type_name_plural
        if additional_fields:
            self.returned_fields.extend(additional_fields)

    def format_record(self, record):
        '''
        '''
        post = {}

        for key in iter(record):
            if key in self.returned_fields:
                post[key] = record[key]

        return post

    def make_resource_url(self, resource_id):
        '''
        '''
        post = self.reverse_url('browse_{}'.format(self.type_name_plural), resource_id + '/')
        if post.endswith('?'):
            post = post[:-1]

        return post

    @gen.coroutine
    def basic_get(self, resource_id=None):
        '''
        '''
        if not resource_id:
            resource_id = '*'
        elif resource_id.endswith('/') and len(resource_id) > 1:
            resource_id = resource_id[:-1]

        resp = yield ask_solr_by_id(self.type_name, resource_id)

        if 0 == len(resp):
            post = '{} {} not found\n'.format(self.type_name, resource_id)
        else:
            post = []
            for each_record in resp:
                post.append(self.format_record(each_record))

        post = {res['id']: res for res in post}
        post['resources'] = {i: self.make_resource_url(i) for i in iter(post)}

        self.set_header('Server', 'Abbott/{}'.format(ABBOTT_VERSION))
        self.add_header('X-Cantus-Version', 'Cantus/{}'.format(CANTUS_API_VERSION))

        return post

    @gen.coroutine
    def get(self, resource_id=None):
        '''
        '''
        self.write((yield self.basic_get(resource_id)))


class ComplexHandler(TaxonomyHandler):
    '''
    For the "Complex" resource types: cantusid, chant, indexer, and source.
    '''

    LOOKUP = {'feast_id': ('feast', 'name', 'feast'),
              'genre_id': ('genre', 'description', 'genre'),
              'office_id': ('office', 'name', 'office'),
              'source_id': ('source', 'title', 'source'),
              'provenance_id': ('provenance', 'name', 'provenance'),
              'century_id': ('century', 'name', 'century'),
              'notation_style_id': ('notation', 'name', 'notation_style'),
              'segment_id': ('segment', 'name', 'segment'),
              'source_status_id': ('source_status', 'name', 'source_status'),
              'indexers': ('indexer', 'display_name', 'indexers'),
              'editors': ('indexer', 'display_name', 'editors'),
              'proofreaders': ('indexer', 'display_name', 'proofreaders'),
             }
    '''
    For those fields that must be cross-referenced with the "name" field of a taxonomy resource.

    - item 0: the "type" to lookup
    - item 1: the field to replace with
    - item 2: field name to use in output

    Example: ``'genre_id': ('genre', 'description', 'genre')``.

    Replaces the "genre_id" field with the "description" field of a "genre" record, stored in the
    "genre" member on output.
    '''
    # TODO: item 1 will have to be configurable at runtime, because I'm sure some people would
    #       rather read "A" rather than "Antiphon," for example

    @gen.coroutine
    def get(self, resource_id=None):
        '''
        '''
        results = yield self.basic_get(resource_id)
        post = {}

        for record in iter(results):
            if 'resources' == record:
                post[record] = results[record]
                continue

            post[record] = {}
            for field in iter(results[record]):
                if field in ComplexHandler.LOOKUP:
                    # TODO: refactor this to reduce duplication
                    if isinstance(results[record][field], (list, tuple)):
                        for value in results[record][field]:
                            post[record][ComplexHandler.LOOKUP[field][2]] = []
                            resp = yield ask_solr_by_id(ComplexHandler.LOOKUP[field][0], value)
                            if len(resp) > 0:
                                try:
                                    post[record][ComplexHandler.LOOKUP[field][2]].append(resp[0][ComplexHandler.LOOKUP[field][1]])
                                except KeyError:
                                    # usually if the desired "field" isn't in the record we found
                                    post[record][ComplexHandler.LOOKUP[field][2]].append(str(resp[0]))
                        if 0 == len(post[record][ComplexHandler.LOOKUP[field][2]]):
                            # if none of the things in the list ended up being found, we'll clear this out
                            del post[record][ComplexHandler.LOOKUP[field][2]]
                    else:
                        resp = yield ask_solr_by_id(ComplexHandler.LOOKUP[field][0], results[record][field])
                        if len(resp) > 0:
                            post[record][ComplexHandler.LOOKUP[field][2]] = resp[0][ComplexHandler.LOOKUP[field][1]]
                elif field in self.returned_fields:
                    # NB: this generic branch must come after the LOOKUP branch. If it's before,
                    #     LOOKUP fields will be matched in self.returned_fields and they won't be
                    #     looked up.
                    post[record][field] = results[record][field]

            # if it's a Chant and doesn't have a "full_text" entry, we can get it from the cantusid
            if 'full_text' in self.returned_fields and 'full_text' not in post[record] and 'cantus_id' in post[record]:
                resp = yield ask_solr_by_id('cantusid', post[record]['cantus_id'])
                if len(resp) > 0 and 'full_text' in resp[0]:
                    post[record]['full_text'] = resp[0]['full_text']

        # TODO: in chant, how to get feast and feast_desc from the feast_id?
        # TODO: in source, how to get provenance and provenance_detail?
        # TODO: in source, how to get source_status and source_status_desc?

        self.write(post)


class RootHandler(web.RequestHandler):
    '''
    '''

    def get(self):
        '''
        '''

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
        post = {'browse_{}'.format(term): self.reverse_url('browse_{}'.format(term), 'id')
                for term in all_plural_resources}
        self.write({'resources': post})


def make_app():
    '''
    NOTE: these URLs require a terminating /
    TODO: make them not
    '''

    return web.Application([
        web.url(r'/', RootHandler),
        web.URLSpec(r'/cantusids/(.*/)?', handler=ComplexHandler, name='browse_cantusids',
                    kwargs={'type_name': 'cantusid', 'type_name_plural': 'cantusids',
                            'additional_fields': ['incipit', 'full_text', 'genre_id']}),
        web.URLSpec(r'/centuries/(.*/)?', handler=TaxonomyHandler, name='browse_centuries',
                    kwargs={'type_name': 'century', 'type_name_plural': 'centuries'}),
        web.URLSpec(r'/chants/(.*/)?', handler=ComplexHandler, name='browse_chants',
                    kwargs={'type_name': 'chant', 'type_name_plural': 'chants',
                            'additional_fields': {'incipit', 'folio', 'position', 'sequence', 'mode',
                                                  'id', 'cantus_id', 'full_text_simssa', 'full_text',
                                                  'full_text_manuscript', 'volpiano', 'notes',
                                                  'cao_concordances', 'melody_id', 'marginalia',
                                                  'differentia', 'finalis', 'siglum', 'feast_id',
                                                  'genre_id', 'office_id', 'source_id'}}),
        web.URLSpec(r'/feasts/(.*/)?', handler=TaxonomyHandler, name='browse_feasts',
                    kwargs={'type_name': 'feast', 'type_name_plural': 'feasts',
                            'additional_fields': ['date', 'feast_code']}),
        web.URLSpec(r'/genres/(.*/)?', handler=TaxonomyHandler, name='browse_genres',
                    kwargs={'type_name': 'genre', 'type_name_plural': 'genres',
                            'additional_fields': ['mass_or_office']}),
        web.URLSpec(r'/indexers/(.*/)?', handler=ComplexHandler, name='browse_indexers',
                    kwargs={'type_name': 'indexer', 'type_name_plural': 'indexers',
                            'additional_fields': ['display_name', 'given_name', 'family_name',
                                                  'institution',' city', 'country']}),
        web.URLSpec(r'/notations/(.*/)?', handler=TaxonomyHandler, name='browse_notations',
                    kwargs={'type_name': 'notation', 'type_name_plural': 'notations'}),
        web.URLSpec(r'/offices/(.*/)?', handler=TaxonomyHandler, name='browse_offices',
                    kwargs={'type_name': 'office', 'type_name_plural': 'offices'}),
        web.URLSpec(r'/portfolia/(.*/)?', handler=TaxonomyHandler, name='browse_portfolia',
                    kwargs={'type_name': 'portfolio', 'type_name_plural': 'portfolia'}),
        web.URLSpec(r'/provenances/(.*/)?', handler=TaxonomyHandler, name='browse_provenances',
                    kwargs={'type_name': 'provenance', 'type_name_plural': 'provenances'}),
        web.URLSpec(r'/sigla/(.*/)?', handler=TaxonomyHandler, name='browse_sigla',
                    kwargs={'type_name': 'siglum', 'type_name_plural': 'sigla'}),
        web.URLSpec(r'/segments/(.*/)?', handler=TaxonomyHandler, name='browse_segments',
                    kwargs={'type_name': 'segment', 'type_name_plural': 'segments'}),
        web.URLSpec(r'/sources/(.*/)?', handler=ComplexHandler, name='browse_sources',
                    kwargs={'type_name': 'source', 'type_name_plural': 'sources',
                            'additional_fields': ['title', 'rism', 'siglum', 'provenance_id',
                                                  'date', 'century_id', 'notation_style_id',
                                                  'segment_id', 'source_status_id', 'summary',
                                                  'liturgical_occasions', 'description',
                                                  'indexing_notes', 'indexing_date', 'indexers',
                                                  'editors', 'proofreaders']}),
        web.URLSpec(r'/statii/(.*/)?', handler=TaxonomyHandler, name='browse_source_statii',
                    kwargs={'type_name': 'source_status', 'type_name_plural': 'source_statii'}),
        ])


def main():
    '''
    '''

    app = make_app()
    app.listen(8888)
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
