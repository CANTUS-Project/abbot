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


import copy
from collections import namedtuple
from tornado import ioloop, web, gen
import pysolrtornado

SOLR = pysolrtornado.Solr('http://localhost:8983/solr/', timeout=10)
DRUPAL_PATH = 'http://cantus2.uwaterloo.ca'
ABBOTT_VERSION = '0.0.2-dev'
CANTUS_API_VERSION = '0.1.1'
PORT = 8888


def singular_resource_to_plural(singular):
    '''
    Convert the name of a resource type (lilke "feast" or "century") to its plural form (like
    "feasts" or "centuries").

    :param str singular: The resource type's name in singular form.
    :returns: The resource type's name in plural form, or ``None`` if the resource type cannot be
        converted.

    **Examples**

    >>> singular_resource_to_plural('chant')
    'chants'
    >>> singular_resource_to_plural('source_status')
    'source_statii'
    '''
    conversions = {'cantusid': 'cantusids',
                   'century': 'centuries',
                   'chant': 'chants',
                   'feast': 'feasts',
                   'genre': 'genres',
                   'indexer': 'indexers',
                   'notation': 'notations',
                   'office': 'offices',
                   'portfolio': 'portfolia',
                   'provenance': 'provenances',
                   'siglum': 'sigla',
                   'segment': 'segments',
                   'source': 'sources',
                   'source_status': 'source_statii',
                   # for Source
                   'indexers': 'indexers',
                   'proofreaders': 'indexers',
                  }

    if singular in conversions:
        return conversions[singular]
    else:
        return None


@gen.coroutine
def ask_solr_by_id(q_type, q_id):
    '''
    Query the Solr server for a record of "q_type" with an id of "q_id." The values are put directly
    into the Solr "q" parameter, so you may use any syntax allowed by the standard query parser.

    .. note:: This function is a Tornado coroutine, so you must call it with a ``yield`` statement.

    :param str q_type: The "type" field to require of the resource. If you only know the record
        ``id`` you may use ``'*'`` for the ``q_type`` to match a record of any type.
    :param str q_id: The "id" field to require of the resource.

    **Example**

    >>> from tornado import gen
    >>> @gen.coroutine
    ... def func():
    ...     return (yield ask_solr_by_id('genre', '162'))
    ...
    >>> yield func()
    <pysolrtornado results thing>
    '''
    return (yield SOLR.search('+type:{} +id:{}'.format(q_type, q_id)))


class SimpleHandler(web.RequestHandler):
    '''
    For the resource types that were represented in Drupal with its "taxonomy" feature. This class
    is for simple resources that do not contain references to other resources. Complex resources
    that do contain references to other resources should use the :class:`ComplexHandler`. Specify
    the resource type to the initializer at runtime.

    By default, :class:`SimpleHandler` only includes the ``'id'``, ``'name'``, and ``'description'``
    fields. You may specify additional fields to the :meth:`initialize` method.
    '''

    _ALLOWED_METHODS = 'GET, OPTIONS'
    # value of the "Allow" header in response to an OPTIONS request

    _DEFAULT_RETURNED_FIELDS = ['id', 'type', 'name', 'description']
    # I realized there was no reason for the default list to be world-accessible, since it has to be
    # deepcopied anyway, so we'll just do this!

    def initialize(self, type_name, additional_fields=None):  # pylint: disable=arguments-differ
        '''
        :param str type_name: The resource type handled by this instance of :class:`SimpleHandler`
            in singular form.
        :param additional_fields: Optional list of fields to append to ``self.returned_fields``.
        :type additional_fields: list of str
        '''
        self.type_name = type_name
        self.type_name_plural = singular_resource_to_plural(type_name)
        self.returned_fields = copy.deepcopy(SimpleHandler._DEFAULT_RETURNED_FIELDS)
        if additional_fields:
            self.returned_fields.extend(additional_fields)

    def set_default_headers(self):
        '''
        Set the default headers for all requests: Server, X-Cantus-Version.
        '''
        # NOTE: keep this the same as RootHandler.set_default_headers() where relevant
        self.set_header('Server', 'Abbott/{}'.format(ABBOTT_VERSION))
        self.add_header('X-Cantus-Version', 'Cantus/{}'.format(CANTUS_API_VERSION))

    def format_record(self, record):
        '''
        Given a record from a ``pysolr-tornado`` response, prepare a record that only has the fields
        indicated in ``self.return_fields``. Becasue a record from a ``pysolr-tornado`` response is
        simply a dictionary, so really this function makes a new dict with all key-value pairs for
        which the key is in ``self.return_fields``.
        '''
        post = {}

        for key in iter(record):
            if key in self.returned_fields:
                post[key] = record[key]

        return post

    def make_resource_url(self, resource_id, resource_type=None):
        '''
        Make a URL for the "resources" section of the response, with the indicated resource type
        and id. The default resource type corresponds to the resource type this
        :class:`SimpleHandler` was created for.

        :param str resource_id: The "id" of the resource in its URL.
        :param str resource_type: An optional resource type for the URL, in either singular or
            plural form. Plural will be slightly faster.
        :returns: A dynamically created URL to the specified resource, without hostname, with a
            terminating slash.
        :rtype: str
        '''
        if resource_type is None:
            resource_type = self.type_name_plural

        try:
            # hope it's a plural resource_type
            post = self.reverse_url('browse_{}'.format(resource_type), resource_id + '/')
        except KeyError:
            # plural didn't work so try converting from a singular resource_type
            post = self.reverse_url('browse_{}'.format(singular_resource_to_plural(resource_type)),
                                    resource_id + '/')

        # Because reverse_url() uses the regexp there will be an extra "?" at the end, used in the
        # regexp to mean that the "id" part is optional. We don't want the "?" here, because we do
        # have an "id".
        if post.endswith('?'):
            post = post[:-1]

        return post

    @gen.coroutine
    def basic_get(self, resource_id=None):
        '''
        Prepare a basic response for the relevant records. This method queries for the specified
        resources, filters out unwanted fields (those not specified in ``returned_fields``), put a
        URL to this resource in the "resources" member, and set the following headers:

        - Server
        - X-Cantus-Version

        .. note:: This function is a Tornado coroutine, so you must call it with a ``yield`` statement.

        For simple resource types---those that do not contain references to other types of
        resources---this method does all required processing. You may call ``self.write()`` directly
        with this method's return value. Subclasses that process more complex resource types may
        do further processing before returning the results.

        :param str resource_id: The "id" field of the resource to fetch. The default, ``None``, will
            fetch the appropriate amount of resources with arbitrary "id".
        :returns: A dictionary that may be used as the response body. There will always be at least
            one member, ``"resources"``, although when there are no other records it will simply be
            an empty dict.
        :rtype: dict
        '''
        # TODO: how to return a 404 when the resource isn't found?!
        if not resource_id:
            resource_id = '*'
        elif resource_id.endswith('/') and len(resource_id) > 1:
            resource_id = resource_id[:-1]

        resp = yield ask_solr_by_id(self.type_name, resource_id)

        if 0 == len(resp):
            post = []
        else:
            post = []
            for each_record in resp:
                this_record = self.format_record(each_record)
                this_record['type'] = self.type_name
                post.append(this_record)

        post = {res['id']: res for res in post}
        post['resources'] = {i: {'self': self.make_resource_url(i)} for i in iter(post)}

        return post

    @gen.coroutine
    def get(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Response to GET requests. Returns the result of :meth:`basic_get` without modification.

        .. note:: This function is a Tornado coroutine, so you must call it with a ``yield`` statement.
        '''
        self.write((yield self.basic_get(resource_id)))

    def options(self, resource_id=None):
        '''
        Response to OPTIONS requests. Sets the "Allow" header and returns.
        '''
        self.add_header('Allow', SimpleHandler._ALLOWED_METHODS)


XrefLookup = namedtuple('XrefLookup', ['type', 'replace_with', 'replace_to'])
'''
Provide instructions for processing fields that are obtained with by cross-reference to another
resource. The "type" is the value of the "type" field to lookup in Solr; "replace_with" is the name
of the field in a "type"-type record that holds the desired value; "replace_to" is the name of the
field to which that value should be assigned in the response body.
'''
# TODO: item 1 will have to be configurable at runtime, because I'm sure some people would rather
#       read "A" rather than "Antiphon," for example


class ComplexHandler(SimpleHandler):
    '''
    A handler for complex resource types that contain references to other resources. Simple resource
    types that do not refer to other resources should use the :class:`SimpleHandler`. Specify the
    resource type to the initializer at runtime.
    '''

    LOOKUP = {'feast_id': XrefLookup('feast', 'name', 'feast'),
              'genre_id': XrefLookup('genre', 'description', 'genre'),
              'office_id': XrefLookup('office', 'name', 'office'),
              'source_id': XrefLookup('source', 'title', 'source'),
              'provenance_id': XrefLookup('provenance', 'name', 'provenance'),
              'century_id': XrefLookup('century', 'name', 'century'),
              'notation_style_id': XrefLookup('notation', 'name', 'notation_style'),
              'segment_id': XrefLookup('segment', 'name', 'segment'),
              'source_status_id': XrefLookup('source_status', 'name', 'source_status'),
              'indexers': XrefLookup('indexer', 'display_name', 'indexers'),
              'editors': XrefLookup('indexer', 'display_name', 'editors'),
              'proofreaders': XrefLookup('indexer', 'display_name', 'proofreaders'),
             }
    '''
    Instructions for fields cross-referenced with another resource. Refer to the description for
    :const:`XrefLookup`. In this dict, keys are the field that should be replaced.

    Example: ``'genre_id': XrefLookup('genre', 'description', 'genre')``.

    Replaces the "genre_id" field with the "description" field of a "genre" record, stored in the
    "genre" member on output.
    '''

    @gen.coroutine
    def look_up_xrefs(self, record):
        '''
        Given a record, fetch fields that reside in other resources. This uses the substitutions
        indicated by :const:`ComplexHandler.LOOKUP`.

        Two dictionaries are returned:

        - In the first, all the keys in ``self.returned_fields`` are copied without modification.
          All the keys in :const:`ComplexHandler.LOOKUP` are replaced with keys and values as
          indicated in that constant's documentation.
        - In the second are a series of URLs intended to be added to the relevant "resources" member.

        :param dict record: A resource that may have some keys matching a key in
            :const:`ComplexHandler.LOOKUP`.
        :returns: Two new dictionaries. Refer to the note above.
        :rtype: 2-tuple of dict

        **Examples**

        For a "chant" resource:

        >>> in_val = {'genre_id': '162', 'incipit': 'Deux ex machina'}
        >>> result = look_up_xrefs(in_val)
        >>> result[0]
        {'genre': 'Versicle', 'incipit', 'Deus ex machina'}
        >>> result[1]
        {'genre': '/genres/162/'}
        '''
        LOOKUP = ComplexHandler.LOOKUP  # pylint: disable=invalid-name

        post = {}
        resources = {}

        for field in iter(record):
            if field in LOOKUP:
                replace_to = LOOKUP[field].replace_to  # for readability

                if isinstance(record[field], (list, tuple)):
                    post[replace_to] = []

                    for value in record[field]:
                        resp = yield ask_solr_by_id(LOOKUP[field].type, value)
                        if len(resp) > 0 and LOOKUP[field].replace_with in resp[0]:
                            post[replace_to].append(resp[0][LOOKUP[field].replace_with])

                    # if nothing the list was found, remove the empty list
                    if 0 == len(post[replace_to]):
                        del post[replace_to]
                        continue  # avoid writing the "resources" block for a missing xref resource

                else:
                    resp = yield ask_solr_by_id(LOOKUP[field].type, record[field])
                    if len(resp) > 0:
                        post[replace_to] = resp[0][LOOKUP[field].replace_with]
                    else:
                        continue  # avoid writing the "resources" block for a missing xref resource

                # fill in "reources" URLs
                plural = singular_resource_to_plural(LOOKUP[field].replace_to)
                if isinstance(record[field], (list, tuple)):
                    resource_url = [self.make_resource_url(x, plural) for x in record[field]]
                else:
                    resource_url = self.make_resource_url(record[field], plural)
                resources[replace_to] = resource_url

            elif field in self.returned_fields:
                # This is for non-cross-referenced fields. Because cross-referenced fields must
                # also appear in self.returned_fields, this branch must appear after the cross-
                # referencing branch, or else cross-references would never work correctly.
                post[field] = record[field]

        return post, resources

    @gen.coroutine
    def fill_from_cantusid(self, record):
        '''
        For records (chants) with a "cantusid" entry, check if they're missing a field that can be
        filled in with data from the cantusid record. Currently the following fields are filled:
        ``'genre_id'``.

        .. note:: The ``record`` *must* have a "cantusid" key or a :exc:`KeyError` will be raised.

        :param dict record: A record with a "cantusid" key.
        :returns: The record amended with additional fields as possible.
        :rtype: dict
        '''
        # TODO: decide if genre is truly the only thing we can fill
        # TODO: test this method
        #if 'full_text' in self.returned_fields and 'full_text' not in record:
            #resp = yield ask_solr_by_id('cantusid', record['cantus_id'])
            #if len(resp) > 0 and 'full_text' in resp[0]:
                #record['full_text'] = resp[0]['full_text']

        if 'genre_id' in self.returned_fields and 'genre' not in record:
            resp = yield ask_solr_by_id('cantusid', record['cantus_id'])
            if len(resp) > 0 and 'genre_id' in resp[0]:
                resp = yield ask_solr_by_id('genre', resp[0]['genre_id'])
                if len(resp) > 0 and 'name' in resp[0]:
                    record['genre'] = resp[0]['name']

        return record

    @gen.coroutine
    def make_extra_fields(self, record, orig_record):
        '''
        For cross-reference records that require more than one field from the cross-referenced
        record, use this method!

        :param dict record: The record as being prepared for output.
        :param dict orig_record: The record as returned directly from the database (i.e., before
            processing any cross-references).
        :returns: The ``record`` argument with additional fields as possible.
        :rtype: dict
        '''
        # (for Chant) fill in fest_desc if we have a feast_id
        if 'feast_id' in self.returned_fields and 'feast_id' in orig_record:
            resp = yield ask_solr_by_id('feast', orig_record['feast_id'])
            if len(resp) > 0 and 'description' in resp[0]:
                record['feast_desc'] = resp[0]['description']

        # (for Source) fill in source_status_desc if we have a source_status_id (probably never used)
        if 'source_status_id' in self.returned_fields and 'source_status_id' in orig_record:
            resp = yield ask_solr_by_id('source_status', orig_record['source_status_id'])
            if len(resp) > 0 and 'description' in resp[0]:
                record['source_status_desc'] = resp[0]['description']

        return record

    @gen.coroutine
    def get(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Process GET requests for complex record types.

        .. note:: This function is a Tornado coroutine, so you must call it with a ``yield`` statement.
        '''
        results = yield self.basic_get(resource_id)
        post = {'resources': results['resources']}

        for record in iter(results):
            if 'resources' == record:
                continue

            # look up basic fields with ComplexHandler.LOOKUP
            xreffed = yield self.look_up_xrefs(results[record])
            post[record] = xreffed[0]

            # add resources' URLs to "resources" member
            for key, value in xreffed[1].items():
                post['resources'][record][key] = value

            # (for Chant) if missing "full_text" or "genre_id" entry, get them from cantusid
            if 'cantus_id' in post[record]:
                post[record] = yield self.fill_from_cantusid(post[record])

            # fill in extra fields, like descriptions, when relevant
            post[record] = yield self.make_extra_fields(post[record], results[record])

        self.write(post)


class RootHandler(web.RequestHandler):
    '''
    For requests to the root URL (i.e., ``/``).
    '''

    _ALLOWED_METHODS = 'GET, OPTIONS'
    # value of the "Allow" header in response to an OPTIONS request

    def set_default_headers(self):
        '''
        Set the default headers for all requests: Server, X-Cantus-Version.
        '''
        # NOTE: keep this the same as SimpleHandler.set_default_headers() where relevant
        self.set_header('Server', 'Abbott/{}'.format(ABBOTT_VERSION))
        self.add_header('X-Cantus-Version', 'Cantus/{}'.format(CANTUS_API_VERSION))

    def prepare_get(self):
        '''
        Does the actual work for a GET request at '/'. It's a different method for easier testing.
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
        return {'resources': post}

    def get(self):  # pylint: disable=arguments-differ
        '''
        Handle GET requests to the root URL. Returns a "resources" member with URLs to all available
        search and browse URLs.
        '''
        self.write(self.prepare_get())

    def options(self, resource_id=None):
        '''
        Response to OPTIONS requests. Sets the "Allow" header and returns.
        '''
        self.add_header('Allow', SimpleHandler._ALLOWED_METHODS)


# NOTE: these URLs require a terminating /
# TODO: make them not
HANDLERS = [
    web.url(r'/', RootHandler),
    web.URLSpec(r'/cantusids/(.*/)?', handler=ComplexHandler, name='browse_cantusids',
                kwargs={'type_name': 'cantusid',
                        'additional_fields': ['incipit', 'full_text', 'genre_id']}),
    web.URLSpec(r'/centuries/(.*/)?', handler=SimpleHandler, name='browse_centuries',
                kwargs={'type_name': 'century'}),
    web.URLSpec(r'/chants/(.*/)?', handler=ComplexHandler, name='browse_chants',
                kwargs={'type_name': 'chant',
                        'additional_fields': {'incipit', 'folio', 'position', 'sequence', 'mode',
                                              'id', 'cantus_id', 'full_text_simssa', 'full_text',
                                              'full_text_manuscript', 'volpiano', 'notes',
                                              'cao_concordances', 'melody_id', 'marginalia',
                                              'differentia', 'finalis', 'siglum', 'feast_id',
                                              'genre_id', 'office_id', 'source_id'}}),
    web.URLSpec(r'/feasts/(.*/)?', handler=SimpleHandler, name='browse_feasts',
                kwargs={'type_name': 'feast', 'additional_fields': ['date', 'feast_code']}),
    web.URLSpec(r'/genres/(.*/)?', handler=SimpleHandler, name='browse_genres',
                kwargs={'type_name': 'genre', 'additional_fields': ['mass_or_office']}),
    web.URLSpec(r'/indexers/(.*/)?', handler=ComplexHandler, name='browse_indexers',
                kwargs={'type_name': 'indexer',
                        'additional_fields': ['display_name', 'given_name', 'family_name',
                                              'institution', 'city', 'country']}),
    web.URLSpec(r'/notations/(.*/)?', handler=SimpleHandler, name='browse_notations',
                kwargs={'type_name': 'notation'}),
    web.URLSpec(r'/offices/(.*/)?', handler=SimpleHandler, name='browse_offices',
                kwargs={'type_name': 'office'}),
    web.URLSpec(r'/portfolia/(.*/)?', handler=SimpleHandler, name='browse_portfolia',
                kwargs={'type_name': 'portfolio'}),
    web.URLSpec(r'/provenances/(.*/)?', handler=SimpleHandler, name='browse_provenances',
                kwargs={'type_name': 'provenance'}),
    web.URLSpec(r'/sigla/(.*/)?', handler=SimpleHandler, name='browse_sigla',
                kwargs={'type_name': 'siglum'}),
    web.URLSpec(r'/segments/(.*/)?', handler=SimpleHandler, name='browse_segments',
                kwargs={'type_name': 'segment'}),
    web.URLSpec(r'/sources/(.*/)?', handler=ComplexHandler, name='browse_sources',
                kwargs={'type_name': 'source',
                        'additional_fields': ['title', 'rism', 'siglum', 'provenance_id',
                                              'date', 'century_id', 'notation_style_id',
                                              'segment_id', 'source_status_id', 'summary',
                                              'liturgical_occasions', 'description',
                                              'indexing_notes', 'indexing_date', 'indexers',
                                              'editors', 'proofreaders', 'provenance_detail']}),
    web.URLSpec(r'/statii/(.*/)?', handler=SimpleHandler, name='browse_source_statii',
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
