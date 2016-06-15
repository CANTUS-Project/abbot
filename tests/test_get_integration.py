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

import pysolrtornado
from tornado import escape, testing
import unittest

import abbot
from abbot import complex_handler
from abbot import simple_handler
import shared


class TestSimple(shared.TestHandler):
    '''
    Integration tests for the SimpleHandler.get().

    NOTE: the URL used for requests is set in __init__() and used by every test. If you want to
          modify the test for use with ComplexHandler, just set "self._type" to a 2-tuple with the
          singular and plural form of the resource type to test. (E.g., ``('chant', 'chants')``).

    NOTE: you can use "self._browse_url" to access the browse URL for the assigned type.
    '''

    def __init__(self, *args, **kwargs):
        super(TestSimple, self).__init__(*args, **kwargs)
        self._type = ('century', 'centuries')
        self._method = 'GET'

    def setUp(self):
        "Make a SimpleHandler instance for testing."
        super(TestSimple, self).setUp()
        self.solr = self.setUpSolr()
        self._browse_url = self.get_url('/{}/'.format(self._type[1]))

    def add_default_resources(self):
        '''
        Send the three "default" testing records to Solr.
        '''
        self.solr.search_se.add('*', {'id': '6', 'name': 'six', 'type': self._type[0],
                                      'drupal_path': '/{}/6/view.html'.format(self._type[0])})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': self._type[0],
                                      'drupal_path': '/{}/2/view.html'.format(self._type[0])})
        self.solr.search_se.add('*', {'id': '9', 'name': 'nine', 'type': self._type[0],
                                      'drupal_path': '/{}/9/view.html'.format(self._type[0])})

    @testing.gen_test
    def test_browse_request(self):
        '''
        - browse request
        - -Total-Results response header is set properly
        - "sort_order" is correct as per what Solr returns
        - it returns properly-formatted output
        - the default "resources" behaviour is checked later
        '''
        self.add_default_resources()
        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}')

        self.check_standard_header(actual)
        assert actual.headers['X-Cantus-Total-Results'] == '3'
        actual = escape.json_decode(actual.body)
        assert ['6', '2', '9'] == actual['sort_order']
        assert {'id': '6', 'name': 'six', 'type': self._type[0]} == actual['6']
        assert {'id': '2', 'name': 'two', 'type': self._type[0]} == actual['2']
        assert {'id': '9', 'name': 'nine', 'type': self._type[0]} == actual['9']

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
        self.add_default_resources()
        headers = {'X-Cantus-Page': '2', 'X-Cantus-Per-Page': '4', 'X-Cantus-Sort': 'id;desc'}
        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', headers=headers)

        self.check_standard_header(actual)
        assert actual.headers['X-Cantus-Page'] == '2'
        assert actual.headers['X-Cantus-Per-Page'] == '4'
        assert actual.headers['X-Cantus-Sort'] == 'id;desc'
        # the query is modified before submission for a SEARCH query
        if self._method == 'SEARCH':
            self.solr.search.assert_any_call('type:{}  AND  ( *  ) '.format(self._type[0]),
                sort='id desc', start=4, rows=4, df='default_search')
        else:
            self.solr.search.assert_any_call('+type:{} +id:*'.format(self._type[0]),
                sort='id desc', start=4, rows=4, df='default_search')

    @testing.gen_test
    def test_view_request(self):
        '''
        - view request
        - -Include-Resources request header is False, and no "resources" part is returned
        '''
        # NOTE: this "view" request doesn't apply for SEARCH
        if self._method == 'SEARCH':
            return

        self.add_default_resources()
        self.solr.search_se.add('id:7', {'id': '7', 'type': self._type[0]})
        headers = {'X-Cantus-Include-Resources': 'false'}
        url = self.get_url('/{0}/7/'.format(self._type[1]))
        actual = yield self.http_client.fetch(url, method='GET', headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert '7' in actual
        assert 'resources' not in actual
        assert {'id': '7', 'type': self._type[0]} == actual['7']

    @testing.gen_test
    def test_resources_1(self):
        '''
        - -Include-Resources request header is omitted (defaults to True)
        - each resource has its thing in the "resources" block
        '''
        self.add_default_resources()
        exp_ids = ('6', '2', '9')
        exp_urls = ['{0}{1}/{2}/'.format(self._simple_options.server_name, self._type[1], x) for x in exp_ids]
        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}')

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
        self.add_default_resources()
        exp_ids = ('6', '2', '9')
        exp_urls = ['{0}{1}/{2}/view.html'.format(self._simple_options.drupal_url, self._type[0], x) for x in exp_ids]
        headers = {'X-Cantus-Include-Resources': 'true'}
        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', headers=headers)

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

        NOTE: this test includes both "simple" and "complex" tests
        '''
        # NOTE: this test includes both "simple" and "complex" tests, to avoid fragmentation
        self.add_default_resources()

        if self._type[0] == 'century':
            # simple resource
            self.solr.search_se.add('*', {'id': '14', 'type': 'indexer', 'name': 'Bob', 'country': 'CA'})
            exp_fields = ('id', 'type', 'name')

            actual = yield self.http_client.fetch(self.get_url('/indexers/'), method=self._method,
                allow_nonstandard_methods=True, body=b'{"query":"*"}')

            self.check_standard_header(actual)
            self.assertCountEqual(exp_fields, actual.headers['X-Cantus-Fields'].split(','))
            assert 'country' in actual.headers['X-Cantus-Extra-Fields']

        else:
            # complex resource
            self.solr.search_se.add('*', {'id': '14', 'type': 'chant', 'incipit': 'Zzz...'})
            exp_fields = ('id', 'type')
            exp_extra_fields = ('incipit', 'name')

            actual = yield self.http_client.fetch(self.get_url('/chants/'), method=self._method,
                allow_nonstandard_methods=True, body=b'{"query":"*"}')

            self.check_standard_header(actual)
            self.assertCountEqual(exp_fields, actual.headers['X-Cantus-Fields'].split(','))
            self.assertCountEqual(exp_extra_fields, actual.headers['X-Cantus-Extra-Fields'].split(','))

    @testing.gen_test
    def test_fields_request(self):
        '''
        Ensure the X-Cantus-Fields request header works.
        '''
        self.add_default_resources()
        exp_order = ('6', '2', '9')
        exp_fields = ['id', 'type']
        request_header = 'id, type'

        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              body=b'{"query":"*"}',
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
        # NOTE: this "view" request doesn't apply for SEARCH queries
        if self._method == 'SEARCH':
            return

        resource_id = '34324242343423423423423'
        expected_reason = simple_handler._ID_NOT_FOUND.format(self._type[0], resource_id)
        request_url = self.get_url('/{0}/{1}/'.format(self._type[1], resource_id))

        actual = yield self.http_client.fetch(request_url,
                                              method='GET',
                                              raise_error=False)

        self.solr.search.assert_called_with('+type:{0} +id:{1}'.format(self._type[0], resource_id), df='default_search')
        self.check_standard_header(actual)
        assert 404 == actual.code
        assert expected_reason == actual.reason

    @testing.gen_test
    def test_resource_id_invalid(self):
        """
        Returns 422 when the resource ID is invalid.
        Regression test for GitHub issue #87.
        """
        # NOTE: this "view" request doesn't apply for SEARCH queries
        if self._method == 'SEARCH':
            return

        resource_id = '-888_'
        expected_reason = simple_handler._INVALID_ID
        request_url = self.get_url('/{0}/{1}/'.format(self._type[1], resource_id))

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
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': self._type[0]})

        slash = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', raise_error=False)
        noslash = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', raise_error=False)

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
        self.add_default_resources()
        exp_expose_headers = ','.join(abbot.CANTUS_RESPONSE_HEADERS)
        exp_allow_origin = self._simple_options.cors_allow_origin
        headers = {'Origin': self._simple_options.cors_allow_origin}

        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', headers=headers)

        assert 'Origin' == actual.headers['Vary']
        assert exp_expose_headers == actual.headers['Access-Control-Expose-Headers']
        assert exp_allow_origin == actual.headers['Access-Control-Allow-Origin']

    @testing.gen_test
    def test_cors_failure(self):
        '''
        - set "Origin" request header to the something arbitrary
        - the CORS headers are missing
        '''
        self.add_default_resources()
        exp_allow_headers = ','.join(abbot.CANTUS_REQUEST_HEADERS)
        exp_expose_headers = ','.join(abbot.CANTUS_RESPONSE_HEADERS)
        exp_allow_origin = self._simple_options.cors_allow_origin
        headers = {'Origin': 'https://something.arbitrary.example.org'}

        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', headers=headers)

        assert 'Access-Control-Allow-Origin' not in actual.headers
        assert 'Access-Control-Expose-Headers' not in actual.headers

    @testing.gen_test
    def test_solr_unavailable_browse(self):
        '''
        - browse request
        - Solr is unavailable, so pysolr-tornado raises a SolrError
        '''
        self.solr.search.side_effect = pysolrtornado.SolrError('error')
        url = self.get_url('/{0}/'.format(self._type[1]))
        actual = yield self.http_client.fetch(url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', raise_error=False)

        self.check_standard_header(actual)
        assert actual.code == 502
        assert actual.reason == simple_handler._SOLR_502_ERROR

    @testing.gen_test
    def test_solr_unavailable_view(self):
        '''
        - view request
        - Solr is unavailable, so pysolr-tornado raises a SolrError
        '''
        # NOTE: this is a "view" URL so the SEARCH method is not allowed
        if self._method == 'SEARCH':
            return

        self.solr.search.side_effect = pysolrtornado.SolrError('error')
        url = self.get_url('/{0}/7/'.format(self._type[1]))
        actual = yield self.http_client.fetch(url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', raise_error=False)

        self.check_standard_header(actual)
        assert actual.code == 502
        assert actual.reason == simple_handler._SOLR_502_ERROR

    @testing.gen_test
    def test_invalid_resource_1(self):
        '''
        When the resource returned doesn't have an "id" field.
        '''
        self.solr.search_se.add('*', {'type': 'feast'})
        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', raise_error=False)

        assert actual.code == 502
        assert actual.reason == simple_handler._RESOURCE_MISSING_ID

    @testing.gen_test
    def test_invalid_resource_2(self):
        '''
        When the resource returned doesn't have a "type" field.
        '''
        self.solr.search_se.add('*', {'id': '123'})
        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"*"}', raise_error=False)

        assert actual.code == 502
        assert actual.reason == simple_handler._RESOURCE_MISSING_TYPE


class TestComplex(TestSimple):
    '''
    A version of TestSimple that's modified to run the tests with a ComplexHandler.

    This test class also adds tests for functionality that's part of complex but not simple. In
    other words, this class also tests cross-referenced fields.
    '''

    def __init__(self, *args, **kwargs):
        super(TestComplex, self).__init__(*args, **kwargs)
        self._type = ('source', 'sources')

    def add_resource_complex(self):
        '''
        Add a complex of resources for use while testing the ComplexHandler.
        '''
        self.solr.search_se.add('+id:*', {'id': '123', 'type': 'source', 'century_id': '61', 'indexers': ['900', '901']})
        self.solr.search_se.add('+id:*', {'id': '234', 'type': 'source', 'century_id': '62', 'indexers': ['900', '901']})
        self.solr.search_se.add('id:61', {'id': '61', 'type': 'century', 'name': '10th'})
        self.solr.search_se.add('id:62', {'id': '62', 'type': 'century', 'name': '14th'})
        self.solr.search_se.add('id:900', {'id': '900', 'type': 'indexer', 'display_name': 'Danceathon Smith'})
        self.solr.search_se.add('id:901', {'id': '901', 'type': 'indexer', 'display_name': 'Fortitude Johnson'})
        #
        self.solr.search_se.add('id:678', {'id': '678', 'type': 'chant', 'feast_id': '416'})
        self.solr.search_se.add('id:416', {'id': '416', 'type': 'feast', 'name': 'Thanksgiving', 'description': 'turkey dinner'})
        #
        self.solr.search_se.add('id:842', {'id': '842', 'type': 'source', 'source_status_id': '5467'})
        self.solr.search_se.add('id:5467', {'id': '5467', 'type': 'source_status', 'name': 'Fake', 'description': 'This Source does not exist.'})
        #
        self.solr.search_se.add('id:498', {'id': '498', 'type': 'source', 'century_id': '8898981'})

    @testing.gen_test
    def test_xref_resources(self):
        '''
        - results include xreffed fields
        - must look up an Indexer (which is xreffed as a list)
        - must look up a Century (which is xreffed as a single ID
        - includes "resources" block
        '''
        self.add_resource_complex()
        headers = {'X-Cantus-Include-Resources': 'true'}
        exp_ids = ['123', '234']

        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"+id:*"}', headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert len(actual) == 4  # two resources, "resources", and "sort_order"
        assert exp_ids == actual['sort_order']
        assert actual['123'] == {'id': '123', 'type': 'source', 'century': '10th', 'indexers': ['Danceathon Smith', 'Fortitude Johnson']}
        assert actual['234'] == {'id': '234', 'type': 'source', 'century': '14th', 'indexers': ['Danceathon Smith', 'Fortitude Johnson']}
        assert actual['resources']['123'] == {
            'self': 'https://cantus.org/sources/123/',
            'indexers': ['https://cantus.org/indexers/900/', 'https://cantus.org/indexers/901/'],
            'indexers_id': ['900', '901'],
            'century': 'https://cantus.org/centuries/61/',
            'century_id': '61',
        }
        assert actual['resources']['234'] == {
            'self': 'https://cantus.org/sources/234/',
            'indexers': ['https://cantus.org/indexers/900/', 'https://cantus.org/indexers/901/'],
            'indexers_id': ['900', '901'],
            'century': 'https://cantus.org/centuries/62/',
            'century_id': '62',
        }

    @testing.gen_test
    def test_issue_96(self):
        '''
        This is a regression test for GitHub issue #96.

        In this issue, cross-references to Notation resources were found to be incorrect. This test
        is to guarantee proper behaviour for the /sources/ URL.

        NOTE: the important part is the "resources" URL generated for the "notation_style" xref.

        - results include xreffed fields
        - must look up an Indexer (which is xreffed as a list)
        - must look up a Century (which is xreffed as a single ID
        - includes "resources" block
        '''
        self.solr.search_se.add('id:3895', {'type': 'notation', 'name': 'German - neumatic', 'id': '3895'})
        self.solr.search_se.add('id:*', {'type': 'source', 'id': '123', 'notation_style_id': '3895'})
        headers = {'X-Cantus-Include-Resources': 'true'}
        exp_ids = ['123']

        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"+id:*"}', headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert exp_ids == actual['sort_order']
        assert actual['resources']['123']['notation_style'] == 'https://cantus.org/notations/3895/'
        assert actual['resources']['123']['notation_style_id'] == '3895'

    @testing.gen_test
    def test_xref_no_resources(self):
        '''
        Same as previous test BUT doesn't include "resources" block
        '''
        self.add_resource_complex()
        headers = {'X-Cantus-Include-Resources': 'false'}
        exp_ids = ['123', '234']

        actual = yield self.http_client.fetch(self._browse_url, method=self._method,
            allow_nonstandard_methods=True, body=b'{"query":"+id:*"}', headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert len(actual) == 3  # two resources and "sort_order"
        assert exp_ids == actual['sort_order']
        for each_id in exp_ids:
            assert each_id in actual

    @testing.gen_test
    def test_xref_adding_fields(self):
        '''
        - ensure we'll look up the "feast_desc"

        NOTE: we have to use a "chant" for this test, in order to get the proper xrefs
        '''
        # NOTE: this "view" request doesn't apply for SEARCH
        if self._method == 'SEARCH':
            return

        self.add_resource_complex()

        actual = yield self.http_client.fetch(self.get_url('/chants/678/'), method='GET')

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert actual['678']['feast_desc'] == 'turkey dinner'

    @testing.gen_test
    def test_xref_adding_fields(self):
        '''
        - ensure we'll look up the "source_status_desc"
        '''
        # NOTE: this "view" request doesn't apply for SEARCH
        if self._method == 'SEARCH':
            return

        self.add_resource_complex()

        actual = yield self.http_client.fetch(self.get_url('/sources/842/'), method='GET')

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert actual['842']['source_status_desc'] == 'This Source does not exist.'

    @testing.gen_test
    def test_xref_missing_resource(self):
        '''
        - the cross-referenced resource isn't available in Solr
        '''
        # NOTE: this "view" request doesn't apply for SEARCH
        if self._method == 'SEARCH':
            return

        self.add_resource_complex()

        actual = yield self.http_client.fetch(self.get_url('/sources/498/'), method='GET')

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert 'century' not in actual['498']
        assert 'century_id' not in actual['498']


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
        self._method = 'GET'

    def setUp(self):
        super(TestBadRequestHeadersSimple, self).setUp()
        self.solr = self.setUpSolr()
        self._browse_url = self.get_url('/{}/'.format(self._type[1]))

    @testing.gen_test
    def test_per_page_1(self):
        "returns 400 when X-Cantus-Per-Page is set improperly"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': 'force'},
                                              body=b'{"query":""}')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_per_page_2(self):
        "returns 507 when X-Cantus-Per-Page is greater than 100"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': '101'},
                                              body=b'{"query":""}')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(507, actual.code)
        self.assertEqual(simple_handler._INVALID_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_per_page_2(self):
        "returns 507 when X-Cantus-Per-Page is less than 0"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': '-5'},
                                              body=b'{"query":""}')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._TOO_SMALL_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_page_1(self):
        "returns 400 when X-Cantus-Page is set too high"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '10'},
                                              body=b'{"query":"+id:*"}')

        # the SEARCH query gets modified before it hits Solr
        if self._method == 'SEARCH':
            self.solr.search.assert_called_with('type:{}  AND  (  +id:*  ) '.format(self._type[0]), start=90,
                rows=10, df='default_search')
        else:
            self.solr.search.assert_called_with('+type:{} +id:*'.format(self._type[0]), start=90,
                rows=10, df='default_search')
        self.check_standard_header(actual)
        self.assertEqual(409, actual.code)
        self.assertEqual(simple_handler._TOO_LARGE_PAGE, actual.reason)

    @testing.gen_test
    def test_page_2(self):
        "returns 400 when X-Cantus-Page is less than 0"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '-2'},
                                              body=b'{"query":""}')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._TOO_SMALL_PAGE, actual.reason)

    @testing.gen_test
    def test_fields_1(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Fields': 'id, type,price'},
                                              body=b'{"query":""}')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_FIELDS, actual.reason)

    @testing.gen_test
    def test_incl_resources_1(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Include-Resources': 'maybe'},
                                              body=b'{"query":""}')

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._BAD_INCLUDE_RESOURCES, actual.reason)

    @testing.gen_test
    def test_sort_1(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self._browse_url,
                                              method=self._method,
                                              allow_nonstandard_methods=True,
                                              raise_error=False,
                                              headers={'X-Cantus-Sort': 'fuzz^ball'},
                                              body=b'{"query":""}')

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
        # NOTE: this test doesn't apply for SEARCH requests, so we'll skip it in that case
        if self._method == 'SEARCH':
            return

        self.solr.search_se.add('id:7', {'id': '7', 'type': self._type[0]})
        headers = {'X-Cantus-Page': 'jj', 'X-Cantus-Per-Page': 'ww', 'X-Cantus-Sort': 'm_l'}
        actual = yield self.http_client.fetch(self.get_url('/{}/7/'.format(self._type[1])),
                                              method='GET',
                                              headers=headers)

        self.check_standard_header(actual)
        actual = escape.json_decode(actual.body)
        assert '7' in actual


class TestBadRequestHeadersComplex(TestBadRequestHeadersSimple):
    '''
    Runs the TestBadRequestHeadersSimple tests with a ComplexHandler.

    There are no tests unique to the ComplexHandler.
    '''

    def __init__(self, *args, **kwargs):
        super(TestBadRequestHeadersComplex, self).__init__(*args, **kwargs)
        self._type = ('source', 'sources')
