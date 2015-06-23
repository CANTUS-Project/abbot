#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbott
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               abbott/util.py
# Purpose:                Utility functions for the Abbott server.
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
Utility functions for the Abbott server.
'''

from tornado import gen
import pysolrtornado


SOLR = pysolrtornado.Solr('http://localhost:8983/solr/', timeout=10)


# error messages for prepare_formatted_sort()
_DISALLOWED_CHARACTER_IN_SORT = '"{}" is not allowed in the "sort" parameter'
_MISSING_DIRECTION_SPEC = 'Could not find a direction ("asc" or "desc") for all sort fields'
_UNKNOWN_FIELD = 'Unknown field for Abbott: "{}"'

# error message for parse_fields_header()
_INVALID_FIELD_NAME = '{} is not a valid field name'

# Used by prepare_formatted_sort(). Put here, they might be used by other methods to check whether
# they have proper values for these things.
ALLOWED_CHARS = ',;_'
DIRECTIONS = ('asc', 'desc')
# TODO: something tells me this list isn't very maintainable, and probably also isn't correct
FIELDS = {'id': 'id',
          'name': 'name',
          'description': 'description',
          'mass_or_office': 'mass_or_office',
          'date': 'date',
          'feast_code': 'feast_code',
          # chant
          'incipit': 'incipit',
          'source': 'source_id',
          'marginalia': 'marginalia',
          'folio': 'folio',
          'sequence': 'sequence',
          'office': 'office_id',
          'genre': 'genre_id',
          'position': 'position',
          'cantus_id': 'cantus_id',
          'feast': 'feast_id',
          'mode': 'mode',
          'differentia': 'differentia',
          'finalis': 'finalis',
          'full_text': 'full_text',
          'full_text_manuscript': 'full_text_manuscript',
          'full_text_simssa': 'full_text_simssa',
          'volpiano': 'volpiano',
          'notes': 'notes',
          'cao_concordances': 'cao_concordances',
          'siglum': 'siglum',
          'proofreader': 'proofreader',
          'melody_id': 'melody_id',
          # source
          'title': 'title',
          'rism': 'rism',
          'provenance': 'provenance_id',
          'century': 'century_id',
          'notation_style': 'notation_style_id',
          'editors': 'editors',
          'indexers': 'indexers',
          'summary': 'summary',
          'liturgical_occasion': 'liturgical_occasion',
          'indexing_notes': 'indexing_notes',
          'indexing_date': 'indexing_date',
          # indexer': '',
          'display_name': 'display_name',
          'given_name': 'given_name',
          'family_name': 'family_name',
          'institution': 'institution',
          'city': 'city',
          'country': 'country'}


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


def prepare_formatted_sort(sort):
    '''
    Prepare the value of an X-Cantus-Sort request header so it may be given to Solr.

    As per the API, the only permitted characters are upper- and lower-case letters, spaces,
    underscores, commas, and semicolons.

    :param str sort: The X-Cantus-Sort header to transform into a Solr "sort" parameter.
    :returns: The sort parameter, formatted for Solr's consumption.
    :rtype: str
    :raises: :exc:`KeyError` when one of the fields in ``sort`` is not a valid field for any of the
        Abbott resource types.
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

        try:
            sort.append('{} {}'.format(FIELDS[field], direction))
        except IndexError:
            raise KeyError(_UNKNOWN_FIELD.format(field))

    sort = ','.join(sort)

    return sort


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

    sort = ';'.join(sort)

    return sort


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

    >>> from abbott import ask_solr_by_id
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
    return (yield SOLR.search('+type:{} +id:{}'.format(q_type, q_id), **extra_params))


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
        if '' == field or 'type' == field or 'id' == field:
            continue
        elif field not in returned_fields:
            raise ValueError(_INVALID_FIELD_NAME.format(field))
        else:
            post.append(field)
    if 'id' not in post:
        post.append('id')
    if 'type' not in post:
        post.append('type')
    return post
