#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbot/complex_handler.py
# Purpose:                ComplexHandler for the Abbot server.
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
ComplexHandler for the Abbot server.
'''

from collections import namedtuple

from tornado.log import app_log as log
from tornado import gen

import pysolrtornado

from abbot import util
from abbot import simple_handler


XrefLookup = namedtuple('XrefLookup', ['type', 'replace_with', 'replace_to'])
'''
Provide instructions for processing fields that are obtained with by cross-reference to another
resource. The "type" is the value of the "type" field to lookup in Solr; "replace_with" is the name
of the field in a "type"-type record that holds the desired value; "replace_to" is the name of the
field to which that value should be assigned in the response body.
'''
# TODO: item 1 will have to be configurable at runtime, because I'm sure some people would rather
#       read "A" rather than "Antiphon," for example


class Xref(object):
    '''
    Holds static methods that handle cross-references.

    This class isn't meant to be instantiated. Rather, it's a container for the functions used in
    preparing cross-references.

    The order of steps in a cross-reference workflow:

    #. :meth:`Xref.collect`
    #. :meth:`Xref.lookup`
    #. :meth:`Xref.fill`
    '''

    @staticmethod
    def collect(record):
        '''
        Step 1: collect the resource IDs to look up.

        :param record: The database record, from Solr, for which we're looking up cross-references.
        :returns: A 2-tuple. First, "record" without any of the cross-reference fields. Second,
            a list of IDs for the cross-reference resources, each prefixed with "id:".
        :rtype: dict, set

        The list of IDs is actually a :func:`set`, to ensure there are no duplicates.
        '''
        post = {}
        xref_query = []

        for field in iter(record):
            if field in ComplexHandler.LOOKUP:
                if isinstance(record[field], (list, tuple)):
                    for each_id in record[field]:
                        xref_query.append('id:{0}'.format(each_id))
                else:
                    xref_query.append('id:{0}'.format(record[field]))
            else:
                post[field] = record[field]

        return post, set(xref_query)

    @staticmethod
    @gen.coroutine
    def lookup(xref_query):
        '''
        Step 2: look up all the cross-reference resources at once.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        :param xref_query: The second element in the 2-tuple returned by :meth:`collect`. This is an
            iterable of strings that contain the resource IDs to retrieve from Solr. Each resource
            ID should be prefaced with ``'id:'``, like ``'id:123'``.
        :returns: The cross-reference resources from Solr. In the dictionary, resource IDs are keys,
            and the resources themselves are values.
        :rtype: dict

        If ``xref_query`` is an empty list, this method returns an empty dictionary.

        This method also returns an empty dictionary (and emits a log message) if the Solr request
        fails. While this will return incomplete data to the user agent (because the cross-referenced
        fields will be missing) it will be better than returning no data.
        '''
        post = {}

        if len(xref_query):
            try:
                xreffed = yield util.search_solr(' OR '.join(xref_query), rows=len(xref_query))
            except pysolrtornado.SolrError as err:
                log.warn('Solr problem: {0}'.format(err.args[0]))
                xreffed = []

            for result in xreffed:
                post[result['id']] = result

        return post

    @staticmethod
    def fill(record, result, xrefs):
        '''
        Step 3: fill in the cross-referenced fields.

        :param record:  The database record, from Solr, for which we're looking up cross-references.
            This should be identical to the "record" parameter given to :meth:`collect`.
        :param result: The first element in the 2-tuple returned by :meth:`collect`. This is the
            record we're filling cross-references into, without any of the fields that will be
            cross-referenced.
        :param xrefs: The return value of :meth:`lookup`, containing the cross-reference resources
            from Solr. Resource IDs are keys, and the resources themselves are values.
        :returns: The "result" argument with cross-reference fields filled in.
        '''
        if xrefs:
            for field in iter(record):
                if field in ComplexHandler.LOOKUP:
                    # for readability
                    replace_to = ComplexHandler.LOOKUP[field].replace_to
                    replace_with = ComplexHandler.LOOKUP[field].replace_with
                    xref_id = record[field]

                    if isinstance(xref_id, list):
                        xreffed = []
                        for each_xref_id in xref_id:
                            if each_xref_id in xrefs:
                                xreffed.append(xrefs[each_xref_id][replace_with])

                        if xreffed:
                            result[replace_to] = xreffed

                    elif xref_id in xrefs:
                        result[replace_to] = xrefs[xref_id][replace_with]

        return result

    @staticmethod
    def resources(record, result, xrefs, make_resource_url):
        '''
        Step 4: fill in the cross-references resources links

        :param record:  The database record, from Solr, for which we're looking up cross-references.
            This should be identical to the "record" parameter given to :meth:`collect`.
        :param result: The first element in the 2-tuple returned by :meth:`collect`. This is the
            record we're filling cross-references into, without any of the fields that will be
            cross-referenced.
        :param xrefs: The return value of :meth:`lookup`, containing the cross-reference resources
            from Solr. Resource IDs are keys, and the resources themselves are values.
        :param make_resource_url: The :func:`ComplexHandler.make_resource_url` function for the
            :class:`ComplexHandler` instance calling this static method.
        :type make_resource_url: function
        :returns: A dictionary for the "resources" part of a Cantus API response. For each cross-
            reference that was found, this includes a link to the resource itself, and a field with
            that resource's ID.

        Example return value:

        ```{'century': 'http://example.org/552', 'century_id': '552'}```
        '''
        post = {}

        if xrefs:
            for field in iter(record):
                if field in ComplexHandler.LOOKUP:
                    # for readability
                    replace_to = ComplexHandler.LOOKUP[field].replace_to
                    xref_id = record[field]
                    plural = util.singular_resource_to_plural(ComplexHandler.LOOKUP[field].type)

                    if isinstance(xref_id, list):
                        urls = []
                        for each_xref_id in xref_id:
                            if each_xref_id in xrefs:
                                urls.append(make_resource_url(each_xref_id, plural))
                        if urls:
                            post[replace_to] = urls
                            post['{0}_id'.format(replace_to)] = xref_id

                    elif xref_id in xrefs:
                        post[replace_to] = make_resource_url(xref_id, plural)
                        post['{0}_id'.format(replace_to)] = xref_id

        return post

class ComplexHandler(simple_handler.SimpleHandler):
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
    def look_up_xrefs(self, results, include_resources):
        '''
        Given the results of a query, fetch fields that reside in other resources. This uses the
        substitutions indicated by :const:`ComplexHandler.LOOKUP`.

        The return value is the response body---in other words, the "results" argument with cross-
        referenced fields substituted and appropriate "resources" information added.

        :param dict record: A resource that may have some keys matching a key in
            :const:`ComplexHandler.LOOKUP`.
        :param bool include_resources: Whether to include the "resources" block.
        :returns: Two new dictionaries. Refer to the note above.
        :rtype: 2-tuple of dict
        '''

        post = {}
        if include_resources:
            resources = results['resources']

        # 1: collect all the resource IDs we need to look up
        xref_query = set()
        for each_id, each_result in results.items():
            if each_id in ('sort_order', 'resources'):
                continue
            collected = Xref.collect(each_result)
            post[each_id] = collected[0]
            xref_query = xref_query.union(collected[1])

        # 2: look up all the cross-reference resources at once
        xrefs = yield Xref.lookup(xref_query)

        for each_id, each_result in results.items():
            if each_id in ('sort_order', 'resources'):
                continue
            # 3: fill in the cross-referenced fields
            filled = Xref.fill(each_result, post[each_id], xrefs)
            post[each_id] = filled

            # 4: fill in the cross-references resources links
            if include_resources:
                resources[each_id].update(Xref.resources(each_result, filled, xrefs, self.make_resource_url))

        # 5: copy over last-minute things
        post['sort_order'] = results['sort_order']
        if include_resources:
            post['resources'] = resources

        return post

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
            resp = yield util.ask_solr_by_id('feast', orig_record['feast_id'])
            if len(resp) > 0 and 'description' in resp[0]:
                record['feast_desc'] = resp[0]['description']

        # (for Source) fill in source_status_desc if we have a source_status_id (probably never used)
        if 'source_status_id' in self.returned_fields and 'source_status_id' in orig_record:
            resp = yield util.ask_solr_by_id('source_status', orig_record['source_status_id'])
            if len(resp) > 0 and 'description' in resp[0]:
                record['source_status_desc'] = resp[0]['description']

        return record

    @gen.coroutine
    def get_handler(self, resource_id=None, query=None):  # pylint: disable=arguments-differ
        '''
        Process GET requests for complex record types.

        :param resource_id: As per :meth:`SimpleHandler.get_handler`
        :param query: As per :meth:`SimpleHandler.get_handler`
        :returns: As per :meth:`SimpleHandler.get_handler`

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        .. note:: This method returns ``None`` in some situations when an error has been returned
            to the client. In those situations, callers of this method must not call :meth:`write()`
            or similar.
        '''
        results, num_results = yield self.basic_get(resource_id=resource_id, query=query)
        if results is None:
            return results, num_results

        post = {'sort_order': results['sort_order']}
        if self.hparams['include_resources']:
            post['resources'] = results['resources']

        post = yield self.look_up_xrefs(results, self.hparams['include_resources'])

        for record in results['sort_order']:
            # fill in extra fields, like descriptions, when relevant
            post[record] = yield self.make_extra_fields(post[record], results[record])

        return post, num_results

    def _lookup_name_for_response(self, name):
        '''
        Look up the ``name`` of a field as returned by the Solr database. Return the name that it
        should have when given to the user agent.

        This is an overridden version of the method in :class:`SimpleHandler`. This version will
        look up the field name in :const:`ComplexHandler.LOOKUP`.

        :param str name: a field name from Solr
        :returns: the corresponding field name for user agents
        :rtype: str
        '''
        if name in ComplexHandler.LOOKUP:
            return ComplexHandler.LOOKUP[name].replace_to
        else:
            return name
