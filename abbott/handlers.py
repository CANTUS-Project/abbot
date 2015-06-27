#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/handlers.py
# Purpose:                HTTP handlers for the Abbott server.
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
HTTP handlers for the Abbott server.
'''

import copy
from collections import defaultdict, namedtuple

from tornado import gen, web
import pysolrtornado

import abbott
from abbott import util


class SimpleHandler(web.RequestHandler):
    '''
    For the resource types that were represented in Drupal with its "taxonomy" feature. This class
    is for simple resources that do not contain references to other resources. Complex resources
    that do contain references to other resources should use the :class:`ComplexHandler`. Specify
    the resource type to the initializer at runtime.

    By default, :class:`SimpleHandler` only includes the ``'id'``, ``'name'``, and ``'description'``
    fields. You may specify additional fields to the :meth:`initialize` method.
    '''

    _ALLOWED_METHODS = 'GET, HEAD, OPTIONS'
    # value of the "Allow" header in response to an OPTIONS request

    _MANY_BAD_HEADERS = 'Multiple Invalid Headers'
    # as advertised

    _INVALID_PER_PAGE = 'Invalid "X-Cantus-Per-Page" header'
    # when the X-Cantus-Per-Page value doesn't work in a call to int()

    _TOO_BIG_PER_PAGE = '"X-Cantus-Per-Page" is too high'
    # when X-Cantus-Per-Page is greater than _MAX_PER_PAGE

    _TOO_SMALL_PER_PAGE = '"X-Cantus-Per-Page" must be 0 or greater'
    # when X-Cantus-Per-Page is less than 0

    _INVALID_PAGE = 'Invalid "X-Cantus-Page" header'
    # when the X-Cantus-Page value doesn't work in a call to int()

    _TOO_SMALL_PAGE = '"X-Cantus-Page" must be greater than 0'
    # when X-Cantus-Page is less than 1

    _TOO_LARGE_PAGE = '"X-Cantus-Page" is too high (there are not that many pages)'
    # when we've gone off the last page

    _ID_NOT_FOUND = 'No {} has id "{}"'
    # when the "id" is...

    _DISALLOWED_CHARACTER_IN_SORT = 'Found a disallowed character in the X-Cantus-Sort header'
    # X-Cantus-Sort contains an invalid character

    _MISSING_DIRECTION_SPEC = 'Could not find a direction ("asc" or "desc") for all sort fields'
    # X-Cantus-Sort has a field that's missing a direction

    _UNKNOWN_FIELD = 'Unknown field name in X-Cantus-Sort'
    # X-Cantus-Sort wants to sort on a field that doesn't exist

    _INVALID_NO_XREF = 'X-Cantus-No-Xref must be either "true" or "false"'
    # X-Cantus-No-Xref doesn't contain any sort of 'true' or 'false'

    _INVALID_FIELDS = 'X-Cantus-Fields header has field name(s) invalid for this resource type'
    # X-Cantus-Fields has fields that don't exist in this resource type

    _SOLR_502_ERROR = 'Bad Gateway (Problem with Solr Server)'
    # when the Solr server has an error

    _DEFAULT_RETURNED_FIELDS = ['id', 'type', 'name', 'description']
    # I realized there was no reason for the default list to be world-accessible, since it has to be
    # deepcopied anyway, so we'll just do this!

    _MAX_PER_PAGE = 100
    # the highest value allowed for X-Cantus-Per-Page; higher values will get a 507

    _HEADERS_FOR_BROWSE = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-Per-Page',
                           'X-Cantus-Page', 'X-Cantus-Sort']
    # the Cantus extension headers that can sensibly be used with a "browse" URL

    _HEADERS_FOR_VIEW = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-No-Xref']
    # the Cantus extension headers that can sensibly be used with a "view" URL

    def __init__(self, *args, **kwargs):
        '''
        Just for the sake of being Pythonic, all the attributes are set to default values here.
        Where relevant, they're initialized with their actual starting values in :meth:`initialize`.
        '''
        # TODO: there are a lot of instance attrs (incl. the Tornado ones) so maybe I should put
        #       some of them into a dict?
        self.field_counts = defaultdict(lambda: 0)
        self.type_name = None  # type name, set by the URL
        self.type_name_plural = None  # set in initialize()
        self.head_request = False  # whether the method being processed is HEAD
        self.total_results = 0  # total number of records to be returned in the response

        # This holds the names of the fields that are appropriate to return for a resource of this
        # type. We start here with the standard field names, and initialize() will add more if
        # required. We do a deep copy so that SimpleHandler._DEFAULT_RETURNED_FIELDS doesn't change
        # through the running time of the program.
        self.returned_fields = copy.deepcopy(SimpleHandler._DEFAULT_RETURNED_FIELDS)

        # request headers (these will hold the parsed and verified values)
        self.per_page = None  # X-Cantus-Per-Page
        self.page = None  # X-Cantus-Page
        self.include_resources = True  # X-Cantus-Include-Resources
        self.sort = None  # X-Cantus-Sort
        self.no_xref = False  # X-Cantus-No-Xrefs
        self.fields = None  # X-Cantus-Fields

        super(SimpleHandler, self).__init__(*args, **kwargs)

    def initialize(self, type_name, additional_fields=None):  # pylint: disable=arguments-differ
        '''
        :param str type_name: The resource type handled by this instance of :class:`SimpleHandler`
            in singular form.
        :param additional_fields: Optional list of fields to append to ``self.returned_fields``.
        :type additional_fields: list of str
        '''
        self.type_name = type_name
        self.type_name_plural = util.singular_resource_to_plural(type_name)

        if additional_fields:
            self.returned_fields.extend(additional_fields)

        # set headers
        if 'X-Cantus-Per-Page' in self.request.headers:
            self.per_page = self.request.headers['X-Cantus-Per-Page']

        if 'X-Cantus-Page' in self.request.headers:
            self.page = self.request.headers['X-Cantus-Page']

        if ('X-Cantus-Include-Resources' in self.request.headers and
            'false' in self.request.headers['X-Cantus-Include-Resources'].lower()):  # pylint: disable=bad-continuation
            self.include_resources = False

        if 'X-Cantus-Sort' in self.request.headers:
            self.sort = self.request.headers['X-Cantus-Sort']

        if 'X-Cantus-No-Xref' in self.request.headers:
            self.no_xref = self.request.headers['X-Cantus-No-Xref']

        if 'X-Cantus-Fields' in self.request.headers:
            self.fields = self.request.headers['X-Cantus-Fields']

    def set_default_headers(self):
        '''
        Set the default headers for all requests: Server, X-Cantus-Version.

        Also sets CORS headers:
        - Access-Control-Allow-Origin (if abbott.DEBUG is True)
        - Access-Control-Allow-Headers
        - Access-Control-Expose-Headers

        .. note:: This method is also used by :meth:`RootHandler.set_default_headers`.
        '''
        self.set_header('Server', 'Abbott/{}'.format(abbott.__version__))
        self.add_header('X-Cantus-Version', 'Cantus/{}'.format(abbott.__cantus_version__))
        if abbott.DEBUG:
            self.add_header('Access-Control-Allow-Origin', 'http://localhost:8000')
        self.add_header('Access-Control-Allow-Headers', ','.join(abbott.CANTUS_REQUEST_HEADERS))
        self.add_header('Access-Control-Expose-Headers', ','.join(abbott.CANTUS_RESPONSE_HEADERS))

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
                self.field_counts[key] += 1

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
            post = self.reverse_url('view_{}'.format(resource_type), resource_id + '/')
        except KeyError:
            # plural didn't work so try converting from a singular resource_type
            post = self.reverse_url('view_{}'.format(util.singular_resource_to_plural(resource_type)),
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
        resources and filters out unwanted fields (those not specified in ``returned_fields``).

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        .. note:: This method returns ``None`` in some situations when an error has been returned
            to the client. In those situations, callers of this method must not call :meth:`write()`
            or similar.

        For simple resource types---those that do not contain references to other types of
        resources---this method does all required processing. You may call ``self.write()`` directly
        with this method's return value. Subclasses that process more complex resource types may
        do further processing before returning the results.

        :param str resource_id: The "id" field of the resource to fetch. The default, ``None``, will
            fetch the appropriate amount of resources with arbitrary "id".
        :returns: A dictionary that may be used as the response body. There will always be at least
            one member, ``"resources"``, although when there are no other records it will simply be
            an empty dict. Returns ``None`` when there are no results, and sends the required
            status code.
        :rtype: dict or NoneType
        '''
        if not resource_id:
            resource_id = '*'
        elif resource_id.endswith('/') and len(resource_id) > 1:
            resource_id = resource_id[:-1]

        # calculate the "start" argument for Solr
        start = None
        if self.page:
            if self.per_page:
                start = (self.page - 1) * self.per_page
            else:
                start = self.page * 10

        if '*' == resource_id:
            # "browse" URLs
            resp = yield util.ask_solr_by_id(self.type_name, resource_id, start=start,
                                             rows=self.per_page, sort=self.sort)
        else:
            # "view" URLs
            resp = yield util.ask_solr_by_id(self.type_name, resource_id)

        if 0 == len(resp):
            if start and resp.hits <= start:
                # if we have 0 results because of a weird "X-Cantus-Page" header, return a 409
                self.send_error(400, reason=SimpleHandler._TOO_LARGE_PAGE)
            else:
                self.send_error(404, reason=SimpleHandler._ID_NOT_FOUND.format(self.type_name, resource_id))  # pylint: disable=line-too-long
            return
        else:
            post = []
            for each_record in resp:
                this_record = self.format_record(each_record)
                this_record['type'] = self.type_name
                post.append(this_record)

        # for the X-Cantus-Total-Results header
        self.total_results = resp.hits

        post = {res['id']: res for res in post}
        if self.include_resources:
            post['resources'] = {i: {'self': self.make_resource_url(i)} for i in iter(post)}

        return post

    @gen.coroutine
    def get_handler(self, resource_id=None):
        '''
        Abstraction layer between :meth:`get` and :meth:`basic_get`. In :class:`SimpleHandler` this
        simply returns the result of :meth:`basic_get`, but :class:`ComplexHandler` does many other
        things here. This abstraction layer allows both handlers to share common header functionality
        in :meth:`basic_get` and response body formatting functionality in :meth:`get`.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        .. note:: This method returns ``None`` in some situations when an error has been returned
            to the client. In those situations, callers of this method must not call :meth:`write()`
            or similar.
        '''
        return (yield self.basic_get(resource_id))

    def verify_request_headers(self, is_browse_request):
        '''
        Ensure that the request headers have valid values.

        .. note:: If this method returns ``False`` you must stop processing the request. Refer to
            the "side effect" explanation below.

        :param bool is_browse_request: Whether the URL accessed for this request is a "browse" URL.
        :returns: ``True`` if all the request headers have valid values, otherwise ``False``.
        :rtype: bool

        **Side Effect**

        If this method discovers an invalid header value, it calls :meth:`send_error` with the
        proper response code and reason, then returns ``False``. Therefore if this method returns
        ``False``, the caller should consider the request to be completely finished, and should not
        continue processing the request.
        '''

        # we'll make this False if we encounter an error
        all_is_well = True

        # we'll compile all the error messages here
        error_messages = []

        if is_browse_request:
            # the API says only to pay attention to these headers for requests to "browse" URLs
            if self.per_page:
                # X-Cantus-Per-Page
                try:
                    self.per_page = int(self.per_page)
                except ValueError:
                    error_messages.append(SimpleHandler._INVALID_PER_PAGE)
                    all_is_well = False
                else:
                    # if "per_page" was already found to be faulty, we don't need to keep checking
                    if self.per_page < 0:
                        error_messages.append(SimpleHandler._TOO_SMALL_PER_PAGE)
                        all_is_well = False
                    elif self.per_page > SimpleHandler._MAX_PER_PAGE:
                        self.send_error(507,
                                        reason=SimpleHandler._TOO_BIG_PER_PAGE,
                                        per_page=SimpleHandler._MAX_PER_PAGE)
                        return False
                    elif 0 == self.per_page:
                        self.per_page = SimpleHandler._MAX_PER_PAGE

            if self.page:
                # X-Cantus-Page
                try:
                    self.page = int(self.page)
                except ValueError:
                    error_messages.append(SimpleHandler._INVALID_PAGE)
                    all_is_well = False
                if all_is_well and self.page < 1:
                    error_messages.append(SimpleHandler._TOO_SMALL_PAGE)
                    all_is_well = False

            if self.sort:
                # X-Cantus-Sort
                try:
                    self.sort = util.prepare_formatted_sort(self.sort)
                except ValueError as val_e:
                    if val_e.args[0] == util._MISSING_DIRECTION_SPEC:
                        error_messages.append(SimpleHandler._MISSING_DIRECTION_SPEC)
                    else:
                        error_messages.append(SimpleHandler._DISALLOWED_CHARACTER_IN_SORT)
                    all_is_well = False
                except KeyError:
                    error_messages.append(SimpleHandler._UNKNOWN_FIELD)
                    all_is_well = False

        if isinstance(self, ComplexHandler) and not isinstance(self.no_xref, bool):
            # X-Cantus-No-Xref
            no_xref = str(self.no_xref).lower().strip()
            if 'true' == no_xref:
                self.no_xref = True
            elif 'false' == no_xref:
                self.no_xref = False
            else:
                error_messages.append(SimpleHandler._INVALID_NO_XREF)
                all_is_well = False

        if self.fields:
            # X-Cantus-Fields
            try:
                self.returned_fields = util.parse_fields_header(self.fields, self.returned_fields)
            except ValueError:
                # probably the field wasn't present
                error_messages.append(SimpleHandler._INVALID_FIELDS)
                all_is_well = False

        if not all_is_well:
            if 1 == len(error_messages):
                self.send_error(400, reason=error_messages[0])
            else:
                self.send_error(400, reason=SimpleHandler._MANY_BAD_HEADERS, body=error_messages)

        return all_is_well

    def make_response_headers(self, is_browse_request, num_records):
        '''
        Prepare the response headers for this request.

        :param bool is_browse_request: Whether the URL accessed for this request is a "browse" URL.
        :param int num_records: The number of records being returned in the response. This is used
            to prepare the ``X-Cantus-Fields`` and ``X-Cantus-Extra-Fields`` headers.

        **Side Effect**

        This method calls :meth:`add_header` many times.
        '''

        # figure out the X-Cantus-Fields and X-Cantus-Extra-Fields headers
        fields = ['type']  # "type" is added by Abbott, so it wouldn't have been counted
        extra_fields = []

        def _lookup_name(name):
            "If relevant, uses ComplexHandler.LOOKUP to adjust the field name."
            if name in ComplexHandler.LOOKUP:
                return ComplexHandler.LOOKUP[name].replace_to
            else:
                return name

        for field in self.field_counts:
            if self.field_counts[field] < num_records:
                extra_fields.append(_lookup_name(field))
            else:
                fields.append(_lookup_name(field))

        if len(fields) > 0:
            self.add_header('X-Cantus-Fields', ','.join(fields))
        if len(extra_fields) > 0:
            self.add_header('X-Cantus-Extra-Fields', ','.join(extra_fields))

        # figure out the X-Cantus-Include-Resources header
        if self.include_resources:
            self.add_header('X-Cantus-Include-Resources', 'true')
        else:
            self.add_header('X-Cantus-Include-Resources', 'false')

        # figure out the X-Cantus-No-Xref header
        if self.no_xref:
            self.add_header('X-Cantus-No-Xref', 'true')

        if is_browse_request:
            # figure out X-Cantus-Total-Results
            self.add_header('X-Cantus-Total-Results', self.total_results)

            # figure out X-Cantus-Per-Page
            if self.per_page:
                self.add_header('X-Cantus-Per-Page', self.per_page)
            else:
                self.add_header('X-Cantus-Per-Page', 10)

            # figure out X-Cantus-Page
            if self.page:
                self.add_header('X-Cantus-Page', self.page)
            else:
                self.add_header('X-Cantus-Page', 1)

            # figure out X-Cantus-Sort
            if self.sort:
                self.add_header('X-Cantus-Sort', util.postpare_formatted_sort(self.sort))

    @gen.coroutine
    def get(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Response to GET requests. Returns the result of :meth:`basic_get` without modification.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        **Side Effects**

        Calls :meth:`verify_request_headers` and :meth:`make_response_headers`. May call
        :meth:`send_error`. Calls :meth:`write` with the response body *only if* ``self.head_request``
        is ``False``.
        '''

        # if there is a resource_id, then this request is to a "view" URL
        is_browse_request = resource_id is None

        # first check the header-set values for sanity
        if not self.verify_request_headers(is_browse_request):
            return

        # run the more specific GET request handler
        try:
            response = yield self.get_handler(resource_id)
            if response is None:
                return
        except pysolrtornado.SolrError:
            # TODO: send back details from the SolrError, once we fully write self.send_error()
            self.send_error(502, reason=SimpleHandler._SOLR_502_ERROR)
            return

        # finally, prepare the response headers
        num_records = (len(response) - 1) if self.include_resources else len(response)
        self.make_response_headers(is_browse_request, num_records)

        if not self.head_request:
            self.write(response)

    @gen.coroutine
    def options(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Response to OPTIONS requests. Sets the "Allow" header and returns.
        '''
        self.add_header('Allow', SimpleHandler._ALLOWED_METHODS)

        if resource_id:
            # "view" URL
            if resource_id.endswith('/') and len(resource_id) > 1:
                resource_id = resource_id[:-1]
            resp = yield util.ask_solr_by_id(self.type_name, resource_id)
            if 0 == len(resp):
                self.send_error(404, reason=SimpleHandler._ID_NOT_FOUND.format(self.type_name, resource_id))  # pylint: disable=line-too-long

            # add Cantus-specific request headers
            for each_header in SimpleHandler._HEADERS_FOR_VIEW:
                self.add_header(each_header, 'allow')
        else:
            # "browse" URL
            # add Cantus-specific request headers
            for each_header in SimpleHandler._HEADERS_FOR_BROWSE:
                self.add_header(each_header, 'allow')

        if isinstance(self, ComplexHandler):
            self.add_header('X-Cantus-No-Xref', 'allow')

    @gen.coroutine
    def head(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Response to HEAD requests. Sets ``self.head_request`` to ``True`` then calls :meth:`get`.
        '''
        self.head_request = True
        yield self.get(resource_id)

    def send_error(self, code, **kwargs):
        '''
        Send an error response to the client.

        :param int code: The response code to use.
        :param str reason: The "reason" for the response code.
        :param int per_page: Optional value to send as the ``X-Cantus-Per-Page`` header.
        '''
        # TODO: test this, after fully rewriting it, as per issue #15
        # TODO: add a "body" argument that takes a list of error messages and does something with it
        self.clear()
        if 'per_page' in kwargs:
            self.add_header('X-Cantus-Per-Page', kwargs['per_page'])
        if 'reason' in kwargs:
            self.set_status(code, kwargs['reason'])
            response = '{}: {}'.format(code, kwargs['reason'])
        else:
            self.set_status(code)
            response = str(code)
        self.write(response)

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

                if not self.no_xref:
                    # X-Cantus-No-Xref: false (usual case)
                    if isinstance(record[field], (list, tuple)):
                        post[replace_to] = []

                        for value in record[field]:
                            resp = yield util.ask_solr_by_id(LOOKUP[field].type, value)
                            if len(resp) > 0 and LOOKUP[field].replace_with in resp[0]:
                                post[replace_to].append(resp[0][LOOKUP[field].replace_with])

                        # if nothing the list was found, remove the empty list
                        if 0 == len(post[replace_to]):
                            del post[replace_to]
                            continue  # avoid writing the "resources" block for a missing xref resource

                    else:
                        resp = yield util.ask_solr_by_id(LOOKUP[field].type, record[field])
                        if len(resp) > 0:
                            post[replace_to] = resp[0][LOOKUP[field].replace_with]
                        else:
                            continue  # avoid writing the "resources" block for a missing xref resource
                else:
                    # X-Cantus-No-Xref: true
                    post[field] = record[field]

                # fill in "reources" URLs
                if self.include_resources:
                    plural = util.singular_resource_to_plural(LOOKUP[field].replace_to)
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
        if self.no_xref:
            return record

        # TODO: decide if genre is truly the only thing we can fill
        # TODO: test this method
        #if 'full_text' in self.returned_fields and 'full_text' not in record:
            #resp = yield util.ask_solr_by_id('cantusid', record['cantus_id'])
            #if len(resp) > 0 and 'full_text' in resp[0]:
                #record['full_text'] = resp[0]['full_text']

        if 'genre_id' in self.returned_fields and 'genre' not in record:
            resp = yield util.ask_solr_by_id('cantusid', record['cantus_id'])
            if len(resp) > 0 and 'genre_id' in resp[0]:
                resp = yield util.ask_solr_by_id('genre', resp[0]['genre_id'])
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
        if self.no_xref:
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
    def get_handler(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Process GET requests for complex record types.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        .. note:: This method returns ``None`` in some situations when an error has been returned
            to the client. In those situations, callers of this method must not call :meth:`write()`
            or similar.
        '''
        results = yield self.basic_get(resource_id)
        if results is None:
            return

        if self.include_resources:
            post = {'resources': results['resources']}
        else:
            post = {}

        for record in iter(results):
            if 'resources' == record:
                continue

            # look up basic fields with ComplexHandler.LOOKUP
            xreffed = yield self.look_up_xrefs(results[record])
            post[record] = xreffed[0]

            # add resources' URLs to "resources" member
            if self.include_resources:
                for key, value in xreffed[1].items():
                    post['resources'][record][key] = value

            # (for Chant) if missing "full_text" or "genre_id" entry, get them from cantusid
            if 'cantus_id' in post[record]:
                post[record] = yield self.fill_from_cantusid(post[record])

            # fill in extra fields, like descriptions, when relevant
            post[record] = yield self.make_extra_fields(post[record], results[record])

        return post


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
            this_url = self.reverse_url('view_{}'.format(resource_type), 'id')
            post['view'][resource_type] = this_url
            post['browse'][resource_type] = this_url[:-3]
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
