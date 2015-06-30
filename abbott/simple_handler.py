#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/simple_handler.py
# Purpose:                SimpleHandler for the Abbott server.
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
SimpleHandler for the Abbott server.
'''

import copy
from collections import defaultdict
import importlib

from tornado import escape, gen, web
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

    SUPPORTED_METHODS = web.RequestHandler.SUPPORTED_METHODS + ('SEARCH',)
    # this registers the SEARCH method as something that Tornado can do

    _ALLOWED_BROWSE_METHODS = 'GET, HEAD, OPTIONS, SEARCH'
    # value of the "Allow" header in response to an OPTIONS request on a "browse" URL

    _ALLOWED_VIEW_METHODS = 'GET, HEAD, OPTIONS'
    # value of the "Allow" header in response to an OPTIONS request on a "view" URL

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
                           'X-Cantus-Page', 'X-Cantus-Sort', 'X-Cantus-Search-Help']
    # the Cantus extension headers that can sensibly be used with a "browse" URL

    _HEADERS_FOR_VIEW = ['X-Cantus-Include-Resources', 'X-Cantus-Fields']
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
    def basic_get(self, resource_id=None, query=None):
        # TODO: tests for "query" functionality
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
        :param str query: The "query" to send to Solr. If this argument is provided, ``resource_id``
            will be ignored.
        :returns: A dictionary that may be used as the response body. There will always be at least
            one member, ``"resources"``, although when there are no other records it will simply be
            an empty dict. Returns ``None`` when there are no results, and sends the required
            status code.
        :rtype: dict or NoneType
        '''

        # prepare the query -------------------------------
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

        # run the query -----------------------------------
        if query:
            # SEARCH method
            resp = yield util.search_solr(query, start=start, rows=self.per_page, sort=self.sort)
        elif '*' == resource_id:
            # "browse" URLs
            resp = yield util.ask_solr_by_id(self.type_name, resource_id, start=start,
                                             rows=self.per_page, sort=self.sort)
        else:
            # "view" URLs
            resp = yield util.ask_solr_by_id(self.type_name, resource_id)

        # format the query --------------------------------
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
        return (yield self.basic_get(resource_id=resource_id))

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

    def _lookup_name_for_response(self, name):
        '''
        Look up the ``name`` of a field as returned by the Solr database. Return the name that it
        should have when given to the user agent.

        This method exists at class-level so the :class:`ComplexHandler` can override it to adjust
        cross-referenced field names. In the :class:`SimpleHandler`, the method simply returns its
        argument.

        :param str name: a field name
        :returns: the same field name
        :rtype: str
        '''
        return name

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

        for field in self.field_counts:
            if self.field_counts[field] < num_records:
                extra_fields.append(self._lookup_name_for_response(field))
            else:
                fields.append(self._lookup_name_for_response(field))

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
        Response to GET requests. Returns the result of :meth:`get_handler` without modification.

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

        if resource_id:
            # "view" URL
            self.add_header('Allow', SimpleHandler._ALLOWED_VIEW_METHODS)
            self.add_header('Access-Control-Allow-Methods', SimpleHandler._ALLOWED_VIEW_METHODS)

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
            self.add_header('Allow', SimpleHandler._ALLOWED_BROWSE_METHODS)
            self.add_header('Access-Control-Allow-Methods', SimpleHandler._ALLOWED_BROWSE_METHODS)

            # add Cantus-specific request headers
            for each_header in SimpleHandler._HEADERS_FOR_BROWSE:
                self.add_header(each_header, 'allow')

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

    @gen.coroutine
    def search_handler(self):
        # TODO: tests
        '''
        Prepare a basic response to a search query. This method should be overridden in subclasses,
        if required, to modify the search behaviour.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.
        '''
        print('search_handler() has this request body: {}'.format(self.request.body))

        body = self.request.body
        if len(body) > 1:
            try:
                body = escape.json_decode(self.request.body)
            except ValueError:
                # TODO: return error
                body = {}
        else:
            body = {}

        if 'query' in body:
            query = body['query']
        else:
            query = ''
        return (yield self.basic_get(query='+type:{} {}'.format(self.type_name, query)))

    @gen.coroutine
    def search(self, resource_id=None):
        # TODO: tests
        '''
        Response to SEARCH requests. Returns the result of :meth:`search_handler` without modification.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        :param any resource_id: This is always ignored. We have to keep it for consistency with
            the GET-handling methods, which Tornado requires.

        **Side Effects**

        Does the same header things as get()
        '''

        # every SEARCH query is a sub-type of browse
        is_browse_request = True

        # first check the header-set values for sanity
        if not self.verify_request_headers(is_browse_request):
            return

        # run the more specific SEARCH request handler
        try:
            response = yield self.search_handler()
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
