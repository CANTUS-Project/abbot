#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbot/simple_handler.py
# Purpose:                SimpleHandler for the Abbot server.
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
SimpleHandler for the Abbot server.
'''

import copy
from collections import defaultdict
from urllib.parse import urljoin

from tornado.log import app_log as log
from tornado import escape, gen, web
from tornado.options import options
import pysolrtornado

import abbot
from abbot import util


options.define('drupal_url', type=str, help='see config file for details.')
options.define('cors_allow_origin',
               help='String or list of strings, the permitted "Host" values for a CORS request.',
               type=str,
               default=None)


# translatable strings
# as advertised
_MANY_BAD_HEADERS = 'Multiple Invalid Headers'
# whe X-Cantus-Include-Resources can't be determined to be True or False
_BAD_INCLUDE_RESOURCES = 'Include-Resources header was not "true" or "false"'
# when the X-Cantus-Per-Page value doesn't work in a call to int()
_INVALID_PER_PAGE = 'Invalid "X-Cantus-Per-Page" header'
# when X-Cantus-Per-Page is greater than _MAX_PER_PAGE
_TOO_BIG_PER_PAGE = '"X-Cantus-Per-Page" is too high'
# when X-Cantus-Per-Page is less than 0
_TOO_SMALL_PER_PAGE = '"X-Cantus-Per-Page" must be 0 or greater'
# when the X-Cantus-Page value doesn't work in a call to int()
_INVALID_PAGE = 'Invalid "X-Cantus-Page" header'
# when X-Cantus-Page is less than 1
_TOO_SMALL_PAGE = '"X-Cantus-Page" must be greater than 0'
# when we've gone off the last page
_TOO_LARGE_PAGE = '"X-Cantus-Page" is too high (there are not that many pages)'
# when the "id" is...
_ID_NOT_FOUND = 'No {} has id "{}"'
# X-Cantus-Sort contains an invalid character
_DISALLOWED_CHARACTER_IN_SORT = 'Found a disallowed character in the X-Cantus-Sort header'
# X-Cantus-Sort has a field that's missing a direction
_MISSING_DIRECTION_SPEC = 'Could not find a direction ("asc" or "desc") for all sort fields'
# X-Cantus-Sort wants to sort on a field that doesn't exist
_UNKNOWN_FIELD = 'Unknown field name in X-Cantus-Sort'
# X-Cantus-Fields has fields that don't exist in this resource type
_INVALID_FIELDS = 'X-Cantus-Fields header has field name(s) invalid for this resource type'
# when the SEARCH reqest body is missing or can't be parsed from JSON
_MISSING_SEARCH_BODY = 'Request body was malformed or missing'
# when the Solr server has an error
_SOLR_502_ERROR = 'Bad Gateway (Problem with Solr Server)'
# when there's a SEARCH request with a query that returns no results, and we've decided to give up
_NO_SEARCH_RESULTS = 'SEARCH query returned no results'
# when the search query itself is improperly formatted
_INVALID_SEARCH_QUERY = 'SEARCH query is malformed'
# when the resource ID is invalid
_INVALID_ID = util._INVALID_ID
# when the resource from Solr doesn't have an "id" field
_RESOURCE_MISSING_ID = 'Solr returned a resource without an "id" field.'
# when the resource from Solr doesn't have a "type" field
_RESOURCE_MISSING_TYPE = 'Solr returned a resource without a "type" field.'
# when the search query has a field that's not valid
_INVALID_SEARCH_FIELD = 'Invalid search field: "{}"'


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

    _DEFAULT_RETURNED_FIELDS = ['id', 'type', 'name', 'description']
    # I realized there was no reason for the default list to be world-accessible, since it has to be
    # deepcopied anyway, so we'll just do this!

    _MAX_PER_PAGE = 100
    # the highest value allowed for X-Cantus-Per-Page; higher values will get a 507

    _HEADERS_FOR_BROWSE = ['X-Cantus-Include-Resources', 'X-Cantus-Fields', 'X-Cantus-Per-Page',
                           'X-Cantus-Page', 'X-Cantus-Sort']
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

        # request headers/body params (these will hold the parsed and verified values)
        self.hparams = {  # "hparams" means "header parameters"
            'per_page': None,           # X-Cantus-Per-Page
            'page': None,               # X-Cantus-Page
            'include_resources': True,  # X-Cantus-Include-Resources
            'sort': None,               # X-Cantus-Sort
            'fields': None,             # X-Cantus-Fields
            'search_query': None,        # "query" parameter from SEARCH request body
            }

        super(SimpleHandler, self).__init__(*args, **kwargs)

    def initialize(self, type_name, additional_fields=None):  # pylint: disable=arguments-differ
        '''
        :param str type_name: The resource type handled by this instance of :class:`SimpleHandler`
            in singular form.
        :param additional_fields: Optional list of fields to append to ``self.returned_fields``.
        :type additional_fields: list of str

        **Side Effect**

        If this is a SEARCH request and the request body is not present, or there is no "query"
        member in the request body, :meth:`send_error` will be called and
        ``self.hparams['search_query']`` will stay ``None``. Therefore, if
        ``self.hparams['search_query']`` is ``None`` after this method, and this is a SEARCH request,
        then you must stop processing, and in particular not call :meth:`write` or
        :meth:`send_error`, which will overwrite the existing error values set by this method.
        '''
        self.type_name = type_name
        self.type_name_plural = util.singular_resource_to_plural(type_name)

        if additional_fields:
            self.returned_fields.extend(additional_fields)

        # take settings from headers
        header_to_setting = (('X-Cantus-Per-Page', 'per_page'),
                             ('X-Cantus-Page', 'page'),
                             ('X-Cantus-Include-Resources', 'include_resources'),
                             ('X-Cantus-Sort', 'sort'),
                             ('X-Cantus-Fields', 'fields')
                            )
        self.hparams.update(util.do_dict_transfer(self.request.headers, header_to_setting))

        # set values from request body
        # NOTE: it's important to do this after the header-setting part; the API says header values
        #       in the request body must take precedence over those in headers
        if self.request.method == 'SEARCH':
            # prepare "body" as JSON-parsed-to-dict
            try:
                body = escape.json_decode(self.request.body)
            except ValueError:
                self.send_error(400, reason=_MISSING_SEARCH_BODY)
            else:
                # take settings from members in the request body
                member_to_setting = (('query', 'search_query'),
                                     ('per_page', 'per_page'),
                                     ('page', 'page'),
                                     ('include_resources', 'include_resources'),
                                     ('sort', 'sort'),
                                     ('fields', 'fields')
                                    )
                self.hparams.update(util.do_dict_transfer(body, member_to_setting))

    def set_default_headers(self):
        '''
        Set the default headers for all requests: Server, X-Cantus-Version.

        Also sets CORS headers:
        - Access-Control-Allow-Origin
        - Access-Control-Allow-Headers
        - Access-Control-Expose-Headers

        CORS is implemented as per https://www.w3.org/TR/cors/#resource-processing-model

        .. note:: This method is also used by :meth:`RootHandler.set_default_headers`.
        '''
        self.set_header('Server', 'Abbot/{}'.format(abbot.__version__))
        self.add_header('X-Cantus-Version', 'Cantus/{}'.format(abbot.__cantus_version__))
        if options.cors_allow_origin:
            if self.request.method == 'OPTIONS':
                self._cors_preflight()
            else:
                self._cors_actual()

    def _cors_preflight(self):
        '''
        Add CORS (Cross-Origin Resource Sharing) headers for the preflight request.

        https://www.w3.org/TR/cors/#resource-preflight-requests
        '''
        # step 1
        if 'Origin' not in self.request.headers:
            return

        # step 2
        if self.request.headers['Origin'] not in options.cors_allow_origin:
            return

        # step 3
        if 'Access-Control-Request-Method' in self.request.headers:
            method = self.request.headers['Access-Control-Request-Method']
        else:
            return

        # step 4
        if 'Access-Control-Request-Headers' in self.request.headers:
            header_field_names = self.request.headers['Access-Control-Request-Headers']
            header_field_names = [x.strip() for x in header_field_names.split(',')]
        else:
            header_field_names = []

        # step 5
        if method not in ('HEAD', 'GET', 'OPTIONS', 'SEARCH'):
            return

        # step 6
        valid_headers = [x.lower() for x in abbot.CANTUS_REQUEST_HEADERS]
        for header in header_field_names:
            if header.lower() not in valid_headers:
                return

        # step 7
        self.add_header('Access-Control-Allow-Origin', self.request.headers['Origin'])
        self.add_header('Vary', 'Origin')  # see https://www.w3.org/TR/cors/#resource-implementation

        # step 8
        self.add_header('Access-Control-Max-Age', '86400')  # 24 hours

        # step 9
        self.add_header('Access-Control-Allow-Methods', method)

        # step 10
        if header_field_names:
            self.add_header('Access-Control-Allow-Headers', ','.join(header_field_names))

    def _cors_actual(self):
        '''
        Add CORS (Cross-Origin Resource Sharing) headers for the actual request.

        https://www.w3.org/TR/cors/#resource-requests
        '''
        # step 1
        if 'Origin' not in self.request.headers:
            return

        # step 2
        if self.request.headers['Origin'] not in options.cors_allow_origin:
            return

        # step 3
        self.add_header('Access-Control-Allow-Origin', self.request.headers['Origin'])
        self.add_header('Vary', 'Origin')  # see https://www.w3.org/TR/cors/#resource-implementation

        # step 4
        self.add_header('Access-Control-Expose-Headers', ','.join(abbot.CANTUS_RESPONSE_HEADERS))

    def format_record(self, record):
        '''
        Given a record from a ``pysolr-tornado`` response, prepare a record that only has the fields
        indicated in ``self.return_fields``. Becasue a record from a ``pysolr-tornado`` response is
        simply a dictionary, so really this function makes a new dict with all key-value pairs for
        which the key is in ``self.return_fields``.
        '''
        post = {}

        drupal = options.drupal_url

        for key in iter(record):
            if key in self.returned_fields:
                post[key] = record[key]
                self.field_counts[key] += 1
            elif drupal and key == 'drupal_path':
                post['drupal_path'] = urljoin(options.drupal_url, record[key])

        return post

    def make_resource_url(self, resource_id, resource_type=None):
        '''
        Make a URL for the "resources" section of the response, with the indicated resource type
        and id. The default resource type corresponds to the resource type this
        :class:`SimpleHandler` was created for.

        :param str resource_id: The "id" of the resource in its URL.
        :param str resource_type: An optional resource type for the URL, in either singular or
            plural form. Plural will be slightly faster.
        :returns: A dynamically created URL to the specified resource, including hostname, with a
            terminating slash.
        :rtype: str
        '''
        if resource_type is None:
            resource_type = self.type_name_plural

        try:
            # hope it's a plural resource_type
            resource = 'view_{}'.format(resource_type)
            resource_path = self.reverse_url(resource, resource_id + '/')
        except KeyError:
            # plural didn't work so try converting from a singular resource_type
            resource = 'view_{}'.format(util.singular_resource_to_plural(resource_type))
            resource_path = self.reverse_url(resource, resource_id + '/')

        # Because of the handler configuration, reverse_url() returns something like this:
        #    /chants/125522/?
        # Since the server_name looks like this:
        #    https://cantus.org/
        # We need to remove the first and last characters of our resource_path
        resource_path = resource_path[1:-1]

        # finally, prepend the host-related info to get a FQDN
        return '{server_name}{resource_path}'.format(server_name=options.server_name,
                                                     resource_path=resource_path)

    @gen.coroutine
    def basic_get(self, resource_id=None, query=None):
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
        :returns: A dictionary that may be used as the response body, and the number of resources in
            the response. The dictionary will always have at least one key, ``"resources"``, although
            when there are no other records it will simply be an empty dict. Returns ``None`` when
            there are no results, after sending the appropriate response to the user agent.
        :rtype: (dict, int) or ``(NoneType, 0)``
        '''

        _NONE_ZERO = (None, 0)

        # prepare the query -------------------------------
        if not resource_id:
            resource_id = '*'
        elif resource_id.endswith('/') and len(resource_id) > 1:
            resource_id = resource_id[:-1]

        # calculate the "start" argument for Solr
        start = None
        if self.hparams['page']:
            start = (self.hparams['page'] - 1) * self.hparams['per_page']

        # run the query -----------------------------------
        if query:
            # SEARCH method
            resp = yield util.search_solr(query, start=start, rows=self.hparams['per_page'],
                                          sort=self.hparams['sort'])
        else:
            # "browse" and "view" URLs
            try:
                resp = yield util.ask_solr_by_id(self.type_name, resource_id, start=start,
                                                 rows=self.hparams['per_page'], sort=self.hparams['sort'])
            except ValueError:
                # this means the Cantus ID was invalid
                self.send_error(422, reason=_INVALID_ID)
                return _NONE_ZERO

        # format the query --------------------------------
        if resp.docs:
            post = {}
            for record in resp:
                if 'id' not in record:
                    self.send_error(502, reason=_RESOURCE_MISSING_ID)
                    return _NONE_ZERO
                elif 'type' not in record:
                    self.send_error(502, reason=_RESOURCE_MISSING_TYPE)
                    return _NONE_ZERO
                else:
                    post[record['id']] = self.format_record(record)

            number_of_records = len(post)
            post['sort_order'] = [record['id'] for record in resp]
        else:
            log.debug('SimpleHandler.basic_get() had no results; resource_id="{0}" and query="{1}"'.format(resource_id, query))
            if start and resp.hits <= start:
                # if we have 0 results because of a weird "X-Cantus-Page" header, return a 409
                self.send_error(409, reason=_TOO_LARGE_PAGE)
            elif query:  # assume this is a SEARCH request
                self.send_error(404, reason=_NO_SEARCH_RESULTS)
            else:
                self.send_error(404, reason=_ID_NOT_FOUND.format(self.type_name, resource_id))
            return _NONE_ZERO

        # for the X-Cantus-Total-Results header
        self.total_results = resp.hits

        if self.hparams['include_resources']:
            post['resources'] = {i: {'self': self.make_resource_url(i, post[i]['type'])} for i in post['sort_order']}

        return post, number_of_records

    @gen.coroutine
    def get_handler(self, resource_id=None, query=None):
        '''
        Abstraction layer between :meth:`get` and :meth:`basic_get`. In :class:`SimpleHandler` this
        simply returns the result of :meth:`basic_get`, but :class:`ComplexHandler` does many other
        things here. This abstraction layer allows both handlers to share common functionality.

        :param resource_id: As per :meth:`basic_get`.
        :param query:
        :returns: As per :meth:`basic_get`.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        .. note:: This method returns ``None`` in some situations when an error has been returned
            to the client. In those situations, callers of this method must not call :meth:`write()`
            or similar.
        '''
        return (yield self.basic_get(resource_id=resource_id, query=query))

    # TODO: too many branches
    # TODO: too many statements
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
            if self.hparams['per_page']:
                # X-Cantus-Per-Page
                try:
                    self.hparams['per_page'] = int(self.hparams['per_page'])
                except ValueError:
                    error_messages.append(_INVALID_PER_PAGE)
                    all_is_well = False
                else:
                    # if "per_page" was already found to be faulty, we don't need to keep checking
                    if self.hparams['per_page'] < 0:
                        error_messages.append(_TOO_SMALL_PER_PAGE)
                        all_is_well = False
                    elif self.hparams['per_page'] > SimpleHandler._MAX_PER_PAGE:
                        self.send_error(507,
                                        reason=_TOO_BIG_PER_PAGE,
                                        per_page=SimpleHandler._MAX_PER_PAGE)
                        return False
                    elif self.hparams['per_page'] == 0:
                        self.hparams['per_page'] = SimpleHandler._MAX_PER_PAGE
            else:
                self.hparams['per_page'] = 10

            if self.hparams['page']:
                # X-Cantus-Page
                try:
                    self.hparams['page'] = int(self.hparams['page'])
                except ValueError:
                    error_messages.append(_INVALID_PAGE)
                    all_is_well = False
                if all_is_well and self.hparams['page'] < 1:
                    error_messages.append(_TOO_SMALL_PAGE)
                    all_is_well = False
            else:
                self.hparams['page'] = 1

            if self.hparams['sort']:
                # X-Cantus-Sort
                try:
                    self.hparams['sort'] = util.prepare_formatted_sort(self.hparams['sort'])
                except ValueError as val_e:
                    # TODO: this shouldn't use protected data like this
                    if val_e.args[0] == util._MISSING_DIRECTION_SPEC:
                        error_messages.append(_MISSING_DIRECTION_SPEC)
                    else:
                        error_messages.append(_DISALLOWED_CHARACTER_IN_SORT)
                    all_is_well = False
                except KeyError:
                    error_messages.append(_UNKNOWN_FIELD)
                    all_is_well = False

        else:
            # This is a "view" request, so we should obliterate the sort/page/per_page settings,
            # just in case they might otherwise cause problems for us.
            self.hparams['page'] = None
            self.hparams['per_page'] = None
            self.hparams['sort'] = None

        if self.hparams['include_resources'] is not True:
            # This looks a little weird; True is the defalt value, and if it's been changed, then
            # we need to find "true" or "false" in the string that it's been set to from the request
            include = self.hparams['include_resources'].strip().lower()  # pylint: disable=no-member
            if 'true' in include:
                self.hparams['include_resources'] = True
            elif 'false' in include:
                self.hparams['include_resources'] = False
            else:
                error_messages.append(_BAD_INCLUDE_RESOURCES)
                all_is_well = False

        if self.hparams['fields']:
            # X-Cantus-Fields
            try:
                self.returned_fields = util.parse_fields_header(self.hparams['fields'], self.returned_fields)
            except ValueError:
                # probably the field wasn't present
                error_messages.append(_INVALID_FIELDS)
                all_is_well = False

        if not all_is_well:
            if len(error_messages) == 1:
                self.send_error(400, reason=error_messages[0])
            else:
                self.send_error(400, reason=_MANY_BAD_HEADERS, body=error_messages)

        return all_is_well

    def _lookup_name_for_response(self, name):  # pylint: disable=no-self-use
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
        fields = []
        extra_fields = []

        for field in self.field_counts:
            if self.field_counts[field] < num_records:
                extra_fields.append(self._lookup_name_for_response(field))
            else:
                fields.append(self._lookup_name_for_response(field))

        if fields:
            self.add_header('X-Cantus-Fields', ','.join(fields))
        if extra_fields:
            self.add_header('X-Cantus-Extra-Fields', ','.join(extra_fields))

        # figure out the X-Cantus-Include-Resources header
        if self.hparams['include_resources']:
            self.add_header('X-Cantus-Include-Resources', 'true')
        else:
            self.add_header('X-Cantus-Include-Resources', 'false')

        if is_browse_request:
            # figure out X-Cantus-Total-Results
            self.add_header('X-Cantus-Total-Results', self.total_results)

            # figure out X-Cantus-Per-Page
            if self.hparams['per_page']:
                self.add_header('X-Cantus-Per-Page', self.hparams['per_page'])
            else:
                self.add_header('X-Cantus-Per-Page', 10)

            # figure out X-Cantus-Page
            if self.hparams['page']:
                self.add_header('X-Cantus-Page', self.hparams['page'])
            else:
                self.add_header('X-Cantus-Page', 1)

            # figure out X-Cantus-Sort
            if self.hparams['sort']:
                self.add_header('X-Cantus-Sort', util.postpare_formatted_sort(self.hparams['sort']))

    @util.request_wrapper
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
            response, num_results = yield self.get_handler(resource_id)
            if response is None:
                return
        except pysolrtornado.SolrError:
            # TODO: send back details from the SolrError, once we fully write self.send_error()
            self.send_error(502, reason=_SOLR_502_ERROR)
            return

        # finally, prepare the response headers
        self.make_response_headers(is_browse_request, num_results)

        if not self.head_request:
            self.write(response)


    @util.request_wrapper
    @gen.coroutine
    def options(self, resource_id=None):  # pylint: disable=arguments-differ
        '''
        Response to OPTIONS requests. Sets the "Allow" header and returns.
        '''

        if resource_id:
            # "view" URL
            self.add_header('Allow', SimpleHandler._ALLOWED_VIEW_METHODS)

            if resource_id.endswith('/') and len(resource_id) > 1:
                resource_id = resource_id[:-1]

            try:
                resp = yield util.ask_solr_by_id(self.type_name, resource_id)
            except ValueError:
                self.send_error(422, reason=_INVALID_ID)
                return
            except pysolrtornado.SolrError:
                self.send_error(502, reason=_SOLR_502_ERROR)
                return

            if not resp:
                self.send_error(404, reason=_ID_NOT_FOUND.format(self.type_name, resource_id))

            # add Cantus-specific request headers
            for each_header in SimpleHandler._HEADERS_FOR_VIEW:
                self.add_header(each_header, 'allow')

        else:
            # "browse" URL
            self.add_header('Allow', SimpleHandler._ALLOWED_BROWSE_METHODS)

            # add Cantus-specific request headers
            for each_header in SimpleHandler._HEADERS_FOR_BROWSE:
                self.add_header(each_header, 'allow')

    @util.request_wrapper
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
        :param response: An object to return as the response body. This should either be a string
            or a dict to serialize as a JSON object.
        :type response: str or dict
        :param allow: A value for the "Allow" HTTP response header. Intended for "405 Method Not
            Allowed," but may also be useful in other situations.
        :type allow: list of str
        '''

        self.clear()

        if 'allow' in kwargs:
            self.add_header('Allow', kwargs['allow'])

        if 'per_page' in kwargs:
            self.add_header('X-Cantus-Per-Page', kwargs['per_page'])

        if 'reason' in kwargs:
            self.set_status(code, kwargs['reason'])
        else:
            self.set_status(code)
            kwargs['reason'] = '(no reason given)'

        if 'response' in kwargs:
            response = kwargs['response']
        else:
            response = '{code}: {reason}'.format(code=code, reason=kwargs['reason'])

        self.write(response)

    @gen.coroutine
    def search_handler(self):
        '''
        Conduct a search query.

        :returns: As per :meth:`get_handler`.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        .. note:: This method returns ``None`` in some situations when an error has been returned
            to the client. In those situations, callers of this method must not call :meth:`write()`
            or similar.

        .. note:: The query string is obtained from the "search_query" header parameter.

        This method works for :class:`ComplexHandler` too, where there may be "subqueries" that refer
        to cross-referenced fields.
        '''

        query = 'type:{type} AND ({query})'.format(type=self.type_name, query=self.hparams['search_query'])

        try:
            query = util.parse_query(query)
        except util.InvalidQueryError:
            self.send_error(400, reason=_INVALID_SEARCH_QUERY)
        else:
            try:
                query = util.assemble_query((yield util.run_subqueries(query)))
            except util.InvalidQueryError as iqe:
                self.send_error(404, reason=_NO_SEARCH_RESULTS)
            except ValueError as val_err:
                self.send_error(400, reason=_INVALID_SEARCH_FIELD.format(val_err.the_field))
            else:
                return (yield self.get_handler(query=query))

        # if we reach this point, there was an error code somewhere
        return (None, 0)

    @util.request_wrapper
    @gen.coroutine
    def search(self, resource_id=None):  # pylint: disable=unused-argument
        '''
        Response to SEARCH requests. Returns the result of :meth:`search_handler` without modification.

        .. note:: This method is a Tornado coroutine, so you must call it with a ``yield`` statement.

        :param any resource_id: This is always ignored. We have to keep it for consistency with
            the GET-handling methods, which Tornado requires.

        **Side Effects**

        Does the same header things as get()
        '''

        if resource_id and resource_id != '/':
            self.send_error(405, allow=SimpleHandler._ALLOWED_VIEW_METHODS)
            return

        # If there was no "query" member in the request body, we'll still get called, even though
        # send_error() will already have been called from initialize(). We have to quit now or
        # we'll end up overwriting the error.
        if self.hparams['search_query'] is None:
            return

        # every SEARCH query is a sub-type of browse
        is_browse_request = True

        # first check the header-set values for sanity
        if not self.verify_request_headers(is_browse_request):
            return

        # run the more specific SEARCH request handler
        try:
            response, num_results = yield self.search_handler()
            if response is None:
                return
        except pysolrtornado.SolrError:
            # TODO: send back details from the SolrError, once we fully write self.send_error()
            self.send_error(502, reason=_SOLR_502_ERROR)
            return

        # finally, prepare the response headers
        self.make_response_headers(is_browse_request, num_results)

        self.write(response)
