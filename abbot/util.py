#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbot/util.py
# Purpose:                Utility functions for the Abbot server.
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
Utility functions for the Abbot server.
'''

import re

from tornado import gen
from tornado.log import app_log as log
from tornado.options import options
import pysolrtornado

from abbot import search_grammar


options.define('solr_url', type=str, help='Full URL path to the Solr instance and collection.',
               default='http://localhost:8983/solr/collection1/')


SOLR = pysolrtornado.Solr(options.solr_url, timeout=10)


# error messages for prepare_formatted_sort()
_DISALLOWED_CHARACTER_IN_SORT = '"{}" is not allowed in the "sort" parameter'
_MISSING_DIRECTION_SPEC = 'Could not find a direction ("asc" or "desc") for all sort fields'
_UNKNOWN_FIELD = 'Unknown field for Abbot: "{}"'

# error message for parse_fields_header() and parse_query_components()
_INVALID_FIELD_NAME = '{} is not a valid field name'

# error message for parse_query()
_INVALID_QUERY = 'Invalid search query.'

# Used by prepare_formatted_sort() and parse_query_components(). Put here, they might be used by
# other methods to check whether they have proper values for these things.
ALLOWED_CHARS = ',;_'
DIRECTIONS = ('asc', 'desc')
FIELDS = (
    'id', 'name', 'description', 'mass_or_office', 'date', 'feast_code', 'incipit', 'source',
    'marginalia', 'folio', 'sequence', 'office', 'genre', 'position', 'cantus_id', 'feast',
    'mode', 'differentia', 'finalis', 'full_text', 'full_text_manuscript', 'proofread_fulltext',
    'volpiano', 'notes', 'cao_concordances', 'siglum', 'proofreader', 'melody_id', 'title',
    'rism', 'provenance', 'century', 'notation_style', 'editors', 'indexers', 'summary',
    'liturgical_occasion', 'indexing_notes', 'indexing_date', 'display_name', 'given_name',
    'family_name', 'institution', 'city', 'country', 'type', 'proofread_fulltext_manuscript'
)
# maps fields that must be cross-referenced into the field name it will have after the cross-reference
TRANSFORM_FIELDS = {'source': 'source_id', 'office': 'office_id', 'genre': 'genre_id',
                    'feast': 'feast_id', 'provenance': 'provenance_id', 'century': 'century_id',
                    'notation_style': 'notation_style_id'}
# list of the field names after the cross-reference
TRANSFORMED_FIELDS = [field for field in TRANSFORM_FIELDS.values()]

# Used by run_subqueries() to know whether a field should be searched with a subquery.
XREFFED_FIELDS = ('feast', 'genre', 'office', 'source', 'provenance', 'century', 'notation',
                  'segment', 'source_status', 'portfolio', 'siglum', 'indexers', 'proofreaders')


class InvalidQueryError(ValueError):
    '''
    Raised by the SEARCH request query-parsing functions when an invalid query is detected.
    '''

    pass



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
                   # for "all"
                   '*': '*',
                  }

    if singular in conversions:
        return conversions[singular]
    else:
        return None


def prepare_formatted_sort(sort):
    '''
    Prepare the value of an X-Cantus-Sort request header so it may be given to Solr.

    As per the API, the only permitted characters are upper- and lower-case letters, spaces,
    underscores, commas, and semicolons.

    :param str sort: The X-Cantus-Sort header to transform into a Solr "sort" parameter.
    :returns: The sort parameter, formatted for Solr's consumption.
    :rtype: str
    :raises: :exc:`KeyError` when one of the fields in ``sort`` is not a valid field for any of the
        Abbot resource types.
    :raises: :exc:`ValueError` when a disallowed character is found in ``sort``.
    :raises: :exc:`ValueError` when a direction is not specified for a field.
    '''
    sort = sort.strip()
    sort = sort.replace(' ', '')

    for each_char in sort:
        if each_char not in ALLOWED_CHARS and not each_char.isalpha():
            raise ValueError(_DISALLOWED_CHARACTER_IN_SORT.format(each_char))

    sorts = sort.split(';')
    sort = []

    for each_sort in sorts:
        try:
            field, direction = each_sort.split(',')
        except ValueError:
            raise ValueError(_MISSING_DIRECTION_SPEC)

        if direction not in DIRECTIONS:
            raise ValueError(_MISSING_DIRECTION_SPEC)

        if field in FIELDS:
            if field in TRANSFORM_FIELDS:
                sort.append('{} {}'.format(TRANSFORM_FIELDS[field], direction))
            else:
                sort.append('{} {}'.format(field, direction))
        else:
            raise KeyError(_UNKNOWN_FIELD.format(field))

    return ','.join(sort)


def postpare_formatted_sort(sort):
    '''
    Prepare the "sort" field given to Solr for use in the X-Cantus-Solr response header. This is
    called "postpare" because it's the final of three steps related to using the X-Cantus-Solr
    header:

    #. prepare: call :func:`prepare_formatted_sort`
    #. pare: use the value to call Solr
    #. postpare: call :func:`postpare_formatted_sort`

    Unlike the "prepare" function, this function assumes its input is correct---i.e., that the
    ``sort`` argument only contains valid characters.

    :param str sort: The Solr "search" parameter to transform into an X-Cantus-Sort header.
    :returns: The X-Cantus-Search header, formatted as per the Cantus API.
    '''
    sorts = sort.split(',')
    sort = []

    for each_sort in sorts:
        field, direction = each_sort.split()
        sort.append('{},{}'.format(field, direction))

    return ';'.join(sort)


def parse_fields_header(header, returned_fields):
    '''
    Parse the value of an X-Cantus-Fields request header into a list of strings that contain valid
    field names.

    .. note:: In accordance with the Cantus API, the "id" and "type" fields are always required.
        Therefore they will always be in the returned list, regardless of whether they was in the
        ``header`` argument.

    :param str header: The value of the X-Cantus-Fields request header.
    :param returned_fields: A list of valid field names.
    :type returned_fields: list of str
    :returns: The field names that are requested in the X-Cantus-Fields header.
    :rtype: list of str
    '''
    post = []
    for field in [x.strip() for x in header.split(',')]:
        if field == '' or field == 'type' or field == 'id':
            continue
        elif field in returned_fields:
            post.append(field)
        elif '{}_id'.format(field) in returned_fields:
            post.append('{}_id'.format(field))
        else:
            raise ValueError(_INVALID_FIELD_NAME.format(field))
    if 'id' not in post:
        post.append('id')
    if 'type' not in post:
        post.append('type')
    return post


def do_dict_transfer(from_here, translations):
    '''
    Transfer values from one dict to a new one, changing the key along the way, ignoring keys that
    don't exist in "from_here".

    :param dict from_here: The source dictionary.
    :param iterable translations: A list/tuple of two-element iterables where the first element
        corresponds to a key that might be in "from_here" and the second element is what the key
        should be called in the returned dictionary.
    :returns: New dictionary with renamed keys.
    :rtype: dict

    **Example**

    >>> do_dict_transfer(from_here={'a': 42}, translations=(('a', 'b'), ('c', 'd')))
    {'b': 42}
    '''
    to_here = {}
    for from_key, to_key in translations:
        if from_key in from_here:
            to_here[to_key] = from_here[from_key]
    return to_here


@gen.coroutine
def ask_solr_by_id(q_type, q_id, start=None, rows=None, sort=None):
    '''
    Query the Solr server for a record of "q_type" with an id of "q_id." The values are put directly
    into the Solr "q" parameter, so you may use any syntax allowed by the standard query parser.

    .. note:: This function is a Tornado coroutine, so you must call it with a ``yield`` statement.

    :param str q_type: The "type" field to require of the resource. If you only know the record
        ``id`` you may use ``'*'`` for the ``q_type`` to match a record of any type.
    :param str q_id: The "id" field to require of the resource.
    :param int start: The "start" field to use when calling Solr (i.e., in a list of results, start
        at the ``start``-th result). Default is Solr default (effectively 0).
    :param int rows: The "rows" field to use when calling Solr (i.e., the maximum number of results
        to include for a single search). Default is Solr default (effectively 10).
    :param str sort: The "sort" field to use when calling Solr, like ``'incipit asc'`` or
        ``'cantus_id desc'``. Default is Solr default.
    :returns: Results from the Solr server, in an object that acts like a list of dicts.
    :rtype: :class:`pysolrtornado.Results`
    :raises: :exc:`pysolrtornado.SolrError` when there's an error while connecting to Solr.

    **Example**

    >>> from abbot import ask_solr_by_id
    >>> from tornado import gen
    >>> @gen.coroutine
    ... def func():
    ...     return (yield ask_solr_by_id('genre', '162'))
    ...
    >>> func()
    <pysolrtornado results thing>
    '''
    extra_params = {}
    if start is not None:
        extra_params['start'] = start
    if rows is not None:
        extra_params['rows'] = rows
    if sort is not None:
        extra_params['sort'] = sort

    query = '+type:{} +id:{}'.format(q_type, q_id)
    log.debug("ask_solr_by_id(): '{}'".format(query))
    return (yield SOLR.search(query, **extra_params))


@gen.coroutine
def search_solr(query, start=None, rows=None, sort=None):
    '''
    Query the Solr server.

    .. note:: This function is a Tornado coroutine, so you must call it with a ``yield`` statement.

    :param str query: The query to submit to Solr.
    :param int start: The "start" field to use when calling Solr (i.e., in a list of results, start
        at the ``start``-th result). Default is Solr default (effectively 0).
    :param int rows: The "rows" field to use when calling Solr (i.e., the maximum number of results
        to include for a single search). Default is Solr default (effectively 10).
    :param str sort: The "sort" field to use when calling Solr, like ``'incipit asc'`` or
        ``'cantus_id desc'``. Default is Solr default.
    :returns: Results from the Solr server, in an object that acts like a list of dicts.
    :rtype: :class:`pysolrtornado.Results`
    :raises: :exc:`pysolrtornado.SolrError` when there's an error while connecting to Solr.
    '''
    # TODO: finalize then test this function
    # TODO: make ask_solr_by_id use this as a helper function
    extra_params = {}
    if start is not None:
        extra_params['start'] = start
    if rows is not None:
        extra_params['rows'] = rows
    if sort is not None:
        extra_params['sort'] = sort

    log.info("search_solr() submits '{}'".format(query))
    return (yield SOLR.search(query, df='default_search', **extra_params))


def request_wrapper(func):
    '''
    Use this function as a decorator on subclasses of :class:`~abbot.simple_handler.SimpleHandler`
    or subclasses to prevent mysterious failures when an exception happens. This function calls the
    :meth:`SimpleHandler.send_error` and writes diagnostic information. If the "debug" setting is
    ``True``, a traceback will be printed with :func:`print`. If "debug" is ``False``, a message
    will be added to the log.

    .. note:: That the method being decorated is assumed to be a Tornado coroutine. You must put
        the ``@request_wrapper`` decorator *above* the coroutine decorator, like this:

        @request_wrapper
        @coroutine
        def get(self):
            pass
    '''

    @gen.coroutine
    def decorated(self, *args, **kwargs):
        '''
        Wraps.
        '''

        try:
            yield func(self, *args, **kwargs)
        except (gen.BadYieldError, Exception) as exc:   # pylint: disable=broad-except
            import traceback
            tback = ''.join(traceback.format_exception(type(exc), exc, None))
            if isinstance(exc, gen.BadYieldError):
                tback += 'IMPORTANT: write the @request_wrapper decorator above @gen.coroutine'
            if options.debug:
                # wonderful traceback so I can read it!
                print(tback)
            else:
                # print a nice message to the journal
                log.error(tback)

            self.send_error(500, reason='Programmer Error')

    return decorated


def parse_query(query):
    '''
    Parse a user-submitted query string into a list of field/value tuples.

    :param str query: The raw, user-submitted search query string.
    :returns: A list of parsed query components (see below).
    :rtype: list of 2-tuple of str
    :raises: :exc:`InvalidQueryError` when SOMETHING SOMETHING SOMETHING

    **Return Value**

    This function produces a list of 2-tuples of strings. In each 2-tuple, the first element is a
    field name, and the second element is the field value. If the user's provided query string does
    not specify a field name for some values, the field name "default" is used in the output.

    **Examples**

    >>> parse_query('antiphon')
    [('default', 'antiphon')]
    >>> parse_query('genre:antiphon')
    [('genre', 'antiphon')]
    >>> parse_query('"in taberna" genre:antiphon')
    [('default', '"in taberna"'), ('genre', 'antiphon')]
    >>> parse_query('size: drink:Dunkelweiß')
    (raises InvalidQueryError)
    '''

    try:
        parsed = search_grammar.parse(query)
    except RuntimeError:
        raise InvalidQueryError(_INVALID_QUERY)

    post = []

    for term in parsed.children:
        # each "term" contains the term itself, plus arbitrary spaces
        term = term.children[0].children[0]

        if term.expr_name == 'named_field':
            term = term.children[0]  # idk why
            post.append((term.children[0].text, term.children[2].text))

        else:  # default field
            post.append(('default', term.children[0].text))

    return post


@gen.coroutine
def run_subqueries(components):
    '''
    From the output of :func:`parse_query_components`, run cross-reference subqueries on the relevant
    fields. Returns the query components with cross-referenced fields substituted with the subquery
    result determined most relevant by Solr.

    :param components: The output of :func:`parse_query_components`.
    :type components: list of 2-tuple of str
    :returns: The cross-referenced. query components (see below).
    :rtype: list of 2-tuple of str
    :raises: :exc:`InvalidQueryError` if a cross-referenced field yields no results.

    .. note:: This function is a Tornado coroutine, so you must call it with a ``yield`` statement.

    .. note:: In the future, this function may be modified according to whether server-side search
        help is requested, to modify cross-referenced fields with no results.

    .. note:: This function takes advantage of how :func:`assemble_query` treats the "default"
        field to provide "OR" chunks for subqueries that return multiple results. See below for an
        example.

    **Return Value**

    This function enhances the result of :func:`parse_query_components` by running subqueries and
    substituting the result determined most relevant by Solr. For example, if there is a query for
    a chant resource with the "feast" field, "feast" must be converted to "feast_id" before the full
    query is run, since chant resources do not directly contain a "feast" field. That's what this
    function does.

    **Examples**

    >>> run_subqueries([('default', 'antiphon')])
    [('default', 'antiphon')]
    >>> run_subqueries([('genre': 'antiphon')])
    [('genre_id': '123')]
    >>> run_subqueries([('filling': 'marzipan')])
    [('default', '(filling_id:529^2 OR filling_id:532^1)')]

    In the third example, there are two "filling" resources that match "marzipan," with IDs 529 and
    532. This function uses the order of subquery results to determine term boosting values, joining
    both "filling" IDs with an OR.
    '''

    reffed_comps = []

    for comp in components:
        if comp[0] not in TRANSFORM_FIELDS:
            reffed_comps.append(comp)
        else:
            field = comp[0]
            results = yield search_solr('type:{} AND ({})'.format(field, comp[1]))
            if not results:
                raise InvalidQueryError('No results for cross-referenced field "{}"'.format(field))

            max_boost = len(results)  # so the min_boost is 1
            if max_boost == 1:
                reffed_comps.append((TRANSFORM_FIELDS[field], results[0]['id']))
            else:
                subq_ids = []
                field_name = TRANSFORM_FIELDS[field]
                for i, result in enumerate(results):
                    subq_ids.append('{field}:{id}^{boost}'.format(
                        field=field_name,
                        id=result['id'],
                        boost=(max_boost - i)
                    ))
                reffed_comps.append(('default', '({})'.format(' OR '.join(subq_ids))))

    return reffed_comps


def assemble_query(components):
    '''
    From the output of :func:`run_subqueries`, assemble the (sub)queries into a single string for
    submission to Solr.

    :param components: The output of :func:`run_subqueries`.
    :type components: list of 2-tuple of str
    :returns: The query string to submit to Solr.
    :rtype: str
    '''
    def helper(comp):
        "Prepare a single field:value pair."
        if comp[0] == 'default':
            return comp[1]
        else:
            return '{field}:{value}'.format(field=comp[0], value=comp[1])

    components = [helper(component) for component in components]

    return ' AND '.join(components)
