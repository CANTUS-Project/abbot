#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/test_get_integration.py
# Purpose:                Integration tests for GET requests in SimpleHandler and ComplexHandler.
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
Integration tests for GET requests in SimpleHandler and ComplexHandler.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from tornado import escape, testing
import unittest

import abbot
from abbot import complex_handler
from abbot import simple_handler
import shared


class TestSimple(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.get().

    NOTE: although it ought to be tested with the rest of the SimpleHandler, the get() method has
    unit tests with the rest of ComplexHandler, since parts of that method use ComplexHandler.LOOKUP
    '''

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSimple, self).setUp()
        self.solr = self.setUpSolr()

    def standard_centuries(self):
        '''
        Send the three "default" testing records to Solr.
        '''
        self.solr.search_se.add('*', {'id': '6', 'name': 'six', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '9', 'name': 'nine', 'type': 'century'})

    @testing.gen_test
    def test_browse_request(self):
        '''
        - browse request
        - -Total-Results response header is set properly
        - "sort_order" is correct as per what Solr returns
        - it returns properly-formatted output
        - the default "resources" behaviour is checked later
        '''
        self.standard_centuries()
        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET')

        self.check_standard_header(actual)
        assert actual.headers['X-Cantus-Total-Results'] == '3'
        actual = escape.json_decode(actual.body)
        assert ['6', '2', '9'] == actual['sort_order']
        assert {'id': '6', 'name': 'six', 'type': 'century'} == actual['6']
        assert {'id': '2', 'name': 'two', 'type': 'century'} == actual['2']
        assert {'id': '9', 'name': 'nine', 'type': 'century'} == actual['9']

    @testing.gen_test
    def test_pagination_and_sort(self):
        '''
        - browse request
        - -Page request header is set (to 2)
        - -Per-Page request header is set (to 4)
        - -Sort request header is set (to "id,desc")
        - the proper response headers are returned

        NOTE: because we rely on Solr to do the page/per_page/sort for us, the response won't
              actually include proper results... but I can still check that all the parameters were
              given to Solr as required
        '''
        self.standard_centuries()
        headers = {'X-Cantus-Page': '2', 'X-Cantus-Per-Page': '4', 'X-Cantus-Sort': 'id,desc'}
        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET', headers=headers)

        self.check_standard_header(actual)
        assert actual.headers['X-Cantus-Page'] == '2'
        assert actual.headers['X-Cantus-Per-Page'] == '4'
        assert actual.headers['X-Cantus-Sort'] == 'id,desc'
        self.solr.search.assert_called_with('+type:century +id:*', sort='id desc', start=4, rows=4,
            df='default_search')

    @testing.gen_test
    def test_view_request(self):
        '''
        - view request
        - -Include-Resources request header is False, and no "resources" part is returned
        '''
        self.standard_centuries()
        self.solr.search_se.add('id:7', {'id': '7', 'type': 'century'})
        headers = {'X-Cantus-Include-Resources': 'false'}
        actual = yield self.http_client.fetch(self.get_url('/centuries/7/'), method='GET', headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert '7' in actual
        assert 'resources' not in actual
        assert {'id': '7', 'type': 'century'} == actual['7']

    @testing.gen_test
    def test_resources_1(self):
        '''
        - -Include-Resources request header is omitted (defaults to True)
        - each resource has its thing in the "resources" block
        '''
        self.standard_centuries()
        exp_ids = ('6', '2', '9')
        exp_urls = ['{0}centuries/{1}/'.format(self._simple_options.server_name, x) for x in exp_ids]
        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET')

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert 'resources' in actual
        for i, each_id in enumerate(exp_ids):
            assert each_id in actual
            assert each_id in actual['resources']
            assert actual['resources'][each_id]['self'] == exp_urls[i]

    @testing.gen_test
    def test_resources_2(self):
        '''
        - -Include-Resources request header is specified as True
        - there's a "drupal_url" in the options
        - each resource has its "drupal_path" set
        '''
        self._simple_options.drupal_url = 'http://drupal/'
        self.standard_centuries()
        exp_ids = ('6', '2', '9')
        exp_urls = ['{0}century/{1}'.format(self._simple_options.drupal_url, x) for x in exp_ids]
        headers = {'X-Cantus-Include-Resources': 'true'}
        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET', headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert 'resources' in actual
        for i, each_id in enumerate(exp_ids):
            # check the Drupal URL
            assert actual[each_id]['drupal_path'] == exp_urls[i]

    @testing.gen_test
    def test_fields_response(self):
        '''
        - add a fourth resource that has an extra field
        - run a "browse" request
        - check the -Fields and -Extra-Fields response headers

        NOTE: this test can't use the "century" URL because it has no extra fields
        '''
        self.standard_centuries()
        self.solr.search_se.add('*', {'id': '14', 'type': 'indexer', 'name': 'Bob', 'country': 'CA'})
        exp_fields = ('id', 'type', 'name')

        actual = yield self.http_client.fetch(self.get_url('/indexers/'), method='GET')

        self.check_standard_header(actual)
        self.assertCountEqual(exp_fields, actual.headers['X-Cantus-Fields'].split(','))
        assert 'country' in actual.headers['X-Cantus-Extra-Fields']

    @testing.gen_test
    def test_fields_request(self):
        '''
        Ensure the X-Cantus-Fields request header works.
        '''
        self.standard_centuries()
        exp_order = ('6', '2', '9')
        exp_fields = ['id', 'type']
        request_header = 'id, type'

        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              headers={'X-Cantus-Fields': request_header}
        )

        self.check_standard_header(actual)
        self.assertCountEqual(exp_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        for each_id in exp_order:
            assert 'name' not in actual[each_id]

    @testing.gen_test
    def test_resource_id_not_found(self):
        """
        Returns 404 when the resource ID is not found.
        Regression test for GitHub issue #87.
        """
        resource_id = '34324242343423423423423'
        expected_reason = simple_handler._ID_NOT_FOUND.format('century', resource_id)
        request_url = self.get_url('/centuries/{}/'.format(resource_id))

        actual = yield self.http_client.fetch(request_url,
                                              method='GET',
                                              raise_error=False)

        self.solr.search.assert_called_with('+type:century +id:{}'.format(resource_id), df='default_search')
        self.check_standard_header(actual)
        assert 404 == actual.code
        assert expected_reason == actual.reason

    @testing.gen_test
    def test_resource_id_invalid(self):
        """
        Returns 422 when the resource ID is invalid.
        Regression test for GitHub issue #87.
        """
        # NOTE: named after TestBasicGetUnit.test_basic_get_unit_8().
        resource_id = '-888_'
        expected_reason = simple_handler._INVALID_ID
        request_url = self.get_url('/centuries/{}/'.format(resource_id))

        actual = yield self.http_client.fetch(request_url,
                                              method='GET',
                                              raise_error=False)

        self.check_standard_header(actual)
        assert 0 == self.solr.search.call_count
        assert 422 == actual.code
        assert expected_reason == actual.reason

    @testing.gen_test
    def test_terminating_slash(self):
        '''
        Check that the results returned from the browse URL are the same when the URL ends with a
        slash and when it doesn't. This test doesn't check whether the results are correct.

        Ultimately this is a test of the __main__ module's URL configuration, but that's okay.
        '''
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})

        slash = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET', raise_error=False)
        noslash = yield self.http_client.fetch(self.get_url('/centuries'), method='GET', raise_error=False)

        self.assertEqual(slash.code, noslash.code)
        self.assertEqual(slash.reason, noslash.reason)
        self.assertEqual(slash.headers, noslash.headers)
        self.assertEqual(slash.body, noslash.body)

    @testing.gen_test
    def test_cors_success(self):
        '''
        - set "Origin" request header to the same as "cors_allow_origin" setting
        - it's returned successfully
        '''
        self.standard_centuries()
        exp_allow_headers = ','.join(abbot.CANTUS_REQUEST_HEADERS)
        exp_expose_headers = ','.join(abbot.CANTUS_RESPONSE_HEADERS)
        exp_allow_origin = self._simple_options.cors_allow_origin
        headers = {'Origin': self._simple_options.cors_allow_origin}

        actual = yield self.http_client.fetch(self.get_url('/genres/'), method='GET', headers=headers)

        assert exp_allow_headers == actual.headers['Access-Control-Allow-Headers']
        assert exp_expose_headers == actual.headers['Access-Control-Expose-Headers']
        assert exp_allow_origin == actual.headers['Access-Control-Allow-Origin']

    # TODO: this "CORS failure" test is known to fail as per GitHub issue #39 and should become "unexpected" when that is fixed
    @unittest.expectedFailure
    @testing.gen_test
    def test_cors_failure(self):
        '''
        - set "Origin" request header to the somethign arbitrary
        - the CORS headers are missing
        '''
        self.standard_centuries()
        exp_allow_headers = ','.join(abbot.CANTUS_REQUEST_HEADERS)
        exp_expose_headers = ','.join(abbot.CANTUS_RESPONSE_HEADERS)
        exp_allow_origin = self._simple_options.cors_allow_origin
        headers = {'Origin': self._simple_options.cors_allow_origin}

        actual = yield self.http_client.fetch(self.get_url('/genres/'), method='GET', headers=headers)

        assert 'Access-Control-Allow-Headers' not in actual.headers
        assert 'Access-Control-Expose-Headers' not in actual.headers
        assert 'Access-Control-Allow-Origin' not in actual.headers


class TestComplex(shared.TestHandler):
    '''
    Unit tests for the ComplexHandler.get().
    '''
    # TODO: figure out how to get all the SimpleHandler tests available for ComplexHandler

    def setUp(self):
        super(TestComplex, self).setUp()
        self.solr = self.setUpSolr()

    @testing.gen_test
    def test_get_integration_1(self):
        '''
        With many xreffed fields; feast_description to make up; include 'resources'; and drupal_path.
        '''
        simple_handler.options.drupal_url = 'http://drp'
        record = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                  'mode': '2S', 'type': 'chant'}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre': 'Responsory Verse',
                               'cantus_id': '600482a', 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S',
                               'drupal_path': 'http://drp/chant/357679'},
                    'resources': {'357679': {'self': 'https://cantus.org/chants/357679/',
                                             'genre': 'https://cantus.org/genres/161/',
                                             'feast': 'https://cantus.org/feasts/2378/'}},
                    'sort_order': ['357679'],
        }
        self.solr.search_se.add('id:357679', record)
        self.solr.search_se.add('id:161', {'name': 'V', 'description': 'Responsory Verse'})
        self.solr.search_se.add('id:2378', {'name': 'Jacobi', 'description': 'James the Greater, Aspotle'})

        actual = yield self.http_client.fetch(self.get_url('/chants/357679/'), method='GET')

        self.check_standard_header(actual)
        self.assertEqual(expected, escape.json_decode(actual.body))
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'].lower())

    @testing.gen_test
    def test_get_integration_2(self):
        "for the X-Cantus-Fields and X-Cantus-Extra-Fields headers; and with multiple returns"
        record_a = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                    'mode': '2S', 'type': 'chant'}
        record_b = {'id': '111222', 'genre_id': '161', 'feast_id': '2378', 'mode': '2S',
                    'sequence': 4, 'type': 'chant'}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre': 'Responsory Verse',
                               'cantus_id': '600482a', 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'},
                    '111222': {'id': '111222', 'type': 'chant', 'genre': 'Responsory Verse',
                               'sequence': 4, 'feast': 'Jacobi',
                               'feast_desc': 'James the Greater, Aspotle', 'mode': '2S'},
                    'sort_order': ['357679', '111222'],
        }
        self.solr.search_se.add('*', record_a)
        self.solr.search_se.add('*', record_b)
        self.solr.search_se.add('161', {'name': 'V', 'description': 'Responsory Verse'})
        self.solr.search_se.add('2378', {'name': 'Jacobi', 'description': 'James the Greater, Aspotle'})
        # expected header: X-Cantus-Fields
        exp_cantus_fields = sorted(['id', 'genre', 'mode', 'feast', 'type'])
        # expected header: X-Cantus-Extra-Fields
        exp_extra_fields = sorted(['cantus_id', 'sequence'])

        actual = yield self.http_client.fetch(self.get_url('/chants/'),
                                              method='GET',
                                              headers={'X-Cantus-Include-Resources': 'FalSE'})

        self.assertEqual(exp_cantus_fields, sorted(actual.headers['X-Cantus-Fields'].split(',')))
        self.assertEqual(exp_extra_fields, sorted(actual.headers['X-Cantus-Extra-Fields'].split(',')))
        self.assertEqual('false', actual.headers['X-Cantus-Include-Resources'].lower())
        self.assertEqual(expected, escape.json_decode(actual.body))

    @testing.gen_test
    def test_get_integration_3(self):
        "test_get_integration_1 but with X-Cantus-No-Xref; include 'resources'"
        record = {'id': '357679', 'genre_id': '161', 'cantus_id': '600482a', 'feast_id': '2378',
                  'mode': '2S', 'type': 'chant'}
        expected = {'357679': {'id': '357679', 'type': 'chant', 'genre_id': '161',
                               'cantus_id': '600482a', 'feast_id': '2378', 'mode': '2S'},
                    'resources': {'357679': {'self': 'https://cantus.org/chants/357679/',
                                             'genre': 'https://cantus.org/genres/161/',
                                             'feast': 'https://cantus.org/feasts/2378/'}},
                    'sort_order': ['357679'],
        }
        self.solr.search_se.add('357679', record)

        actual = yield self.http_client.fetch(self.get_url('/chants/357679/'),
                                              method='GET',
                                              headers={'X-Cantus-No-Xref': 'TRUE'})

        self.check_standard_header(actual)
        self.assertEqual(expected, escape.json_decode(actual.body))
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'].lower())
        self.assertEqual('true', actual.headers['X-Cantus-No-Xref'].lower())

    @testing.gen_test
    def test_get_integration_6(self):
        """
        Returns 404 when the resource ID is not found.
        Regression test for GitHub issue #87.
        Named in honour of the test_get_integration_6() for SimpleHandler.
        """
        resource_id = '34324242343423423423423'
        expected_reason = simple_handler._ID_NOT_FOUND.format('chant', resource_id)
        request_url = self.get_url('/chants/{}/'.format(resource_id))

        actual = yield self.http_client.fetch(request_url,
                                              method='GET',
                                              raise_error=False)

        self.solr.search.assert_called_with('+type:chant +id:{}'.format(resource_id), df='default_search')
        self.check_standard_header(actual)
        assert 404 == actual.code
        assert expected_reason == actual.reason


    @testing.gen_test
    def test_get_integration_8(self):
        """
        Returns 404 when the resource ID is not found.
        Regression test for GitHub issue #87.
        """
        # NOTE: named after TestBasicGetUnit.test_basic_get_unit_8().
        # NOTE: corresponds to the same-numbered test in test_simple_handler.py
        resource_id = '-888_'
        expected_reason = simple_handler._INVALID_ID
        request_url = self.get_url('/chants/{}/'.format(resource_id))

        actual = yield self.http_client.fetch(request_url,
                                              method='GET',
                                              raise_error=False)

        self.check_standard_header(actual)
        assert 0 == self.solr.search.call_count
        assert 422 == actual.code
        assert expected_reason == actual.reason


class TestBadRequestHeadersSimple(shared.TestHandler):
    '''
    Tests for when one of the HTTP headers in the request is invalid or improper or broken.

    NOTE: the URL used for requests is set in __init__() and used by every test. If you want to
          modify the test for use with ComplexHandler, just set "self._type" to a 2-tuple with the
          singular and plural form of the resource type to test. (E.g., ``('chant', 'chants')``).

    NOTE: you can use "self._browse_url" to access the browse URL for the assigned type.
    '''

    def __init__(self, *args, **kwargs):
        super(TestBadRequestHeadersSimple, self).__init__(*args, **kwargs)
        self._type = ('century', 'centuries')

    def setUp(self):
        super(TestBadRequestHeadersSimple, self).setUp()
        self.solr = self.setUpSolr()
        self._browse_url = self.get_url('/{}/'.format(self._type[1]))

    @testing.gen_test
    def test_per_page_1(self):
        "returns 400 when X-Cantus-Per-Page is set improperly"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': 'force'})

        assert 0 == self.solr.search.call_count
        # self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_per_page_2(self):
        "returns 507 when X-Cantus-Per-Page is greater than 100"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': '101'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(507, actual.code)
        self.assertEqual(simple_handler._INVALID_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_per_page_2(self):
        "returns 507 when X-Cantus-Per-Page is less than 0"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': '-5'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._TOO_SMALL_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_page_1(self):
        "returns 400 when X-Cantus-Page is set too high"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '10'})

        self.solr.search.assert_called_with('+type:{} +id:*'.format(self._type[0]), start=90, rows=10,
            df='default_search')
        self.check_standard_header(actual)
        self.assertEqual(409, actual.code)
        self.assertEqual(simple_handler._TOO_LARGE_PAGE, actual.reason)

    @testing.gen_test
    def test_page_2(self):
        "returns 400 when X-Cantus-Page is less than 0"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '-2'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._TOO_SMALL_PAGE, actual.reason)

    @testing.gen_test
    def test_fields_1(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Fields': 'id, type,price'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_FIELDS, actual.reason)

    @testing.gen_test
    def test_incl_resources_1(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Include-Resources': 'maybe'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._BAD_INCLUDE_RESOURCES, actual.reason)

    @testing.gen_test
    def test_sort_1(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Sort': 'fuzz^ball'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._DISALLOWED_CHARACTER_IN_SORT, actual.reason)

    @testing.gen_test
    def test_ignored_in_view(self):
        '''
        - -Page, -Per-Page, and -Sort request headers are all invalid
        - but it's a "view" request, so the API says they should be ignored
        '''
        self.solr.search_se.add('id:7', {'id': '7', 'type': self._type[0]})
        headers = {'X-Cantus-Page': 'jj', 'X-Cantus-Per-Page': 'ww', 'X-Cantus-Sort': 'm_l'}
        actual = yield self.http_client.fetch(self.get_url('/{}/7/'.format(self._type[1])), method='GET',
            headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert '7' in actual


class TestBadRequestHeadersComplex(TestBadRequestHeadersSimple):
    '''
    Runs the TestBadRequestHeadersSimple tests with a ComplexHandler.
    '''

    def __init__(self, *args, **kwargs):
        super(TestBadRequestHeadersComplex, self).__init__(*args, **kwargs)
        self._type = ('source', 'sources')

    @testing.gen_test
    def test_noxref_1(self):
        "returns 400 when X-Cantus-No-Xref isn't a boolean setting"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-No-Xref': 'please'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(complex_handler._INVALID_NO_XREF, actual.reason)
