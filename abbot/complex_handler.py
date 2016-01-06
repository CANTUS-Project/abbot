#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbot/complex_handler.py
# Purpose:                ComplexHandler for the Abbot server.
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
ComplexHandler for the Abbot server.
'''

from collections import namedtuple

from tornado.log import app_log as log
from tornado import gen

from abbot import util
from abbot import simple_handler


# translatable strings
_INVALID_NO_XREF = 'X-Cantus-No-Xref must be either "true" or "false"'
# X-Cantus-No-Xref doesn't contain any sort of 'true' or 'false'


XrefLookup = namedtuple('XrefLookup', ['type', 'replace_with', 'replace_to'])
'''
Provide instructions for processing fields that are obtained with by cross-reference to another
resource. The "type" is the value of the "type" field to lookup in Solr; "replace_with" is the name
of the field in a "type"-type record that holds the desired value; "replace_to" is the name of the
field to which that value should be assigned in the response body.
'''
# TODO: item 1 will have to be configurable at runtime, because I'm sure some people would rather
#       read "A" rather than "Antiphon," for example


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

        # TODO: this is too complicated
        for field in iter(record):
            if field in LOOKUP:
                replace_to = LOOKUP[field].replace_to  # for readability

                if not self.hparams['no_xref']:
                    # X-Cantus-No-Xref: false (usual case)
                    if isinstance(record[field], (list, tuple)):
                        post[replace_to] = []

                        for value in record[field]:
                            resp = yield util.ask_solr_by_id(LOOKUP[field].type, value)
                            if len(resp) > 0 and LOOKUP[field].replace_with in resp[0]:
                                post[replace_to].append(resp[0][LOOKUP[field].replace_with])

                        # if nothing the list was found, remove the empty list
                        if not post[replace_to]:
                            del post[replace_to]
                            continue  # avoid writing the "resources" block for a missing xref resource

                    else:
                        resp = yield util.ask_solr_by_id(LOOKUP[field].type, record[field])
                        if resp:
                            post[replace_to] = resp[0][LOOKUP[field].replace_with]
                        else:
                            continue  # avoid writing the "resources" block for a missing xref resource
                else:
                    # X-Cantus-No-Xref: true
                    post[field] = record[field]

                # fill in "reources" URLs
                if self.hparams['include_resources']:
                    plural = util.singular_resource_to_plural(LOOKUP[field].replace_to)
                    if isinstance(record[field], (list, tuple)):
                        resource_url = [self.make_resource_url(x, plural) for x in record[field]]
                    else:
                        resource_url = self.make_resource_url(record[field], plural)
                    resources[replace_to] = resource_url

            elif field in self.returned_fields or field == 'drupal_path':
                # This is for non-cross-referenced fields. Because cross-referenced fields must
                # also appear in self.returned_fields, this branch must appear after the cross-
                # referencing branch, or else cross-references would never work correctly. The one
                # exception is "drupal_path," which won't appear in "returned_fields" because it's
                # not stored in Solr.
                post[field] = record[field]

        return post, resources

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
        if self.hparams['no_xref']:
            return record

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
            return

        post = {'sort_order': results['sort_order']}
        if self.hparams['include_resources']:
            post['resources'] = results['resources']

        for record in results['sort_order']:
            # look up basic fields with ComplexHandler.LOOKUP
            xreffed = yield self.look_up_xrefs(results[record])
            post[record] = xreffed[0]

            # add resources' URLs to "resources" member
            if self.hparams['include_resources']:
                for key, value in xreffed[1].items():
                    post['resources'][record][key] = value

            # fill in extra fields, like descriptions, when relevant
            post[record] = yield self.make_extra_fields(post[record], results[record])

        return post, num_results

    def verify_request_headers(self, is_browse_request):
        '''
        Ensure that the request headers have valid values. This method calls
        :meth:`SimpleHandler.verify_request_headers`, then also checks the X-Cantus-No-Xref header.

        **Please refer to the superclass method's documentation.**
        '''

        all_is_well = super(ComplexHandler, self).verify_request_headers(
            is_browse_request=is_browse_request)

        if all_is_well:
            # X-Cantus-No-Xref
            no_xref = str(self.hparams['no_xref']).lower().strip()
            if no_xref == 'true':
                self.hparams['no_xref'] = True
            elif no_xref == 'false':
                self.hparams['no_xref'] = False
            else:
                self.send_error(400, reason=_INVALID_NO_XREF)
                all_is_well = False

        return all_is_well

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

    @util.request_wrapper
    @gen.coroutine
    def options(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Response to OPTIONS requests. Sets the "Allow" header and returns.
        '''
        yield super(ComplexHandler, self).options(resource_id=resource_id)
        self.add_header('X-Cantus-No-Xref', 'allow')
