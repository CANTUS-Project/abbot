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

    @testing.gen_test
    def test_get_integration_1(self):
        "test_basic_get_unit_1() but through the whole App infrastructure (thus using get())"
        simple_handler.options.drupal_url = 'http://drp'
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '3', 'name': 'three', 'type': 'century'})
        expected = {'1': {'id': '1', 'name': 'one', 'type': 'century', 'drupal_path': 'http://drp/century/1'},
                    '2': {'id': '2', 'name': 'two', 'type': 'century', 'drupal_path': 'http://drp/century/2'},
                    '3': {'id': '3', 'name': 'three', 'type': 'century', 'drupal_path': 'http://drp/century/3'},
                    'resources': {'1': {'self': 'https://cantus.org/centuries/1/'},
                                  '2': {'self': 'https://cantus.org/centuries/2/'},
                                  '3': {'self': 'https://cantus.org/centuries/3/'}},
                    'sort_order': ['1', '2', '3'],
        }
        expected_fields = ['id', 'name', 'type']

        actual = yield self.http_client.fetch(self.get_url('/centuries/'), method='GET')

        self.solr.search.assert_called_once_with('+type:century +id:*', df='default_search', rows=10)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertCountEqual(expected_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_get_integration_2(self):
        "returns 400 when X-Cantus-Per-Page is set improperly"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Per-Page': 'force'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_PER_PAGE, actual.reason)

    @testing.gen_test
    def test_get_integration_3(self):
        "returns 400 when X-Cantus-Page is set too high"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Page': '10'})

        self.solr.search.assert_called_with('+type:century +id:*', start=90, rows=10, df='default_search')
        self.check_standard_header(actual)
        self.assertEqual(409, actual.code)
        self.assertEqual(simple_handler._TOO_LARGE_PAGE, actual.reason)

    @testing.gen_test
    def test_get_integration_4(self):
        "ensure the X-Cantus-Fields request header works"
        self.solr.search_se.add('*', {'id': '1', 'name': 'one', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '2', 'name': 'two', 'type': 'century'})
        self.solr.search_se.add('*', {'id': '3', 'name': 'three', 'type': 'century'})
        expected = {'1': {'id': '1', 'type': 'century'},
                    '2': {'id': '2', 'type': 'century'},
                    '3': {'id': '3', 'type': 'century'},
                    'resources': {'1': {'self': 'https://cantus.org/centuries/1/'},
                                  '2': {'self': 'https://cantus.org/centuries/2/'},
                                  '3': {'self': 'https://cantus.org/centuries/3/'}},
                    'sort_order': ['1', '2', '3'],
        }
        expected_fields = ['id', 'type']
        request_header = 'id, type'

        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              headers={'X-Cantus-Fields': request_header})

        self.solr.search.assert_called_once_with('+type:century +id:*', df='default_search', rows=10)
        self.check_standard_header(actual)
        self.assertEqual('true', actual.headers['X-Cantus-Include-Resources'])
        self.assertEqual('3', actual.headers['X-Cantus-Total-Results'])
        self.assertEqual('1', actual.headers['X-Cantus-Page'])
        self.assertEqual('10', actual.headers['X-Cantus-Per-Page'])
        self.assertCountEqual(expected_fields, actual.headers['X-Cantus-Fields'].split(','))
        actual = escape.json_decode(actual.body)
        self.assertEqual(expected, actual)

    @testing.gen_test
    def test_get_integration_5(self):
        "returns 400 when X-Cantus-Fields has a field name that doesn't exist"
        actual = yield self.http_client.fetch(self.get_url('/centuries/'),
                                              method='GET',
                                              raise_error=False,
                                              headers={'X-Cantus-Fields': 'id, type,price'})

        assert 0 == self.solr.search.call_count
        self.check_standard_header(actual)
        self.assertEqual(400, actual.code)
        self.assertEqual(simple_handler._INVALID_FIELDS, actual.reason)

    @testing.gen_test
    def test_get_integration_6(self):
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
    def test_get_integration_8(self):
        """
        Returns 404 when the resource ID is not found.
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
        Check that the results returned from the root URL are the same when the URL ends with a
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


class TestComplex(shared.TestHandler):
    '''
    Unit tests for the ComplexHandler.get().
    '''

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
