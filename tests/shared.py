#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           abbot
# Program Description:    HTTP Server for the CANTUS Database
#
# Filename:               tests/shared.py
# Purpose:                Shared classes and functions for Abbot's automated test suite.
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
Shared classes and functions for Abbot's automated test suite.
'''
# NOTE: so long as no call is made into the "pysolrtornado" library, which happens when functions
#       "in front of" pysolrtornado are replaced by mocks, the test classes needn't use tornado's
#       asynchronous TestCase classes.

# pylint: disable=protected-access
# That's an important part of testing! For me, at least.

from unittest import mock
from tornado import concurrent, testing, web
from tornado.options import options
import pysolrtornado
import abbot
from abbot import __main__ as main

# ensure we have a consistent "server_name" for all the tests
options.server_name = 'https://cantus.org/'


def make_future(with_this):
    '''
    Creates a new :class:`Future` with the function's argument as the result.
    '''
    val = concurrent.Future()
    val.set_result(with_this)
    return val

def make_results(docs):
    '''
    Create a new :class:`pysolrtornado.Results` instance with the ``docs`` argument as the
    :attr:`docs` attribute. This also sets the proper "hits" attribute.

    :param docs: The actual results returned from Solr.
    :type docs: list of dict
    '''
    return pysolrtornado.Results({'response': {'numFound': len(docs), 'docs': docs}})


def _solr_side_effect(*args, **kwargs):
    '''
    A mock "side effect" for methods on the "util" module's `pysolr-tornado` instance.

    Requests hitting this default mock indicate a test was misconfigured.
    '''
    raise AssertionError('abbot.tests.shared.TestHandler blocks access to Solr; your test is misconfigured')


class TestHandler(testing.AsyncHTTPTestCase):
    "Base class for classes that test a ___Handler."

    def get_app(self):
        return web.Application(main.HANDLERS)

    def check_standard_header(self, on_this):
        '''
        Verify the proper values for the headers that should be part of every response:

        - Server
        - X-Cantus-Version

        :param on_this: The :class:`Response` object to verify.
        :type on_this: :class:`tornado.httpclient.HTTPResponse`
        '''
        exp_server = 'Abbot/{}'.format(abbot.__version__)
        exp_cantus_version = 'Cantus/{}'.format(abbot.__cantus_version__)
        assert exp_server == on_this.headers['Server']
        assert exp_cantus_version == on_this.headers['X-Cantus-Version']

    def setUp(self):
        '''
        Install a mock on the global "options" modules, and the "util" module's `pysolr-tornado`
        instance.

        The following options are mocked in the :mod:`simple_handler` module:

        - drupal_url: None
        - server_name: 'https://cantus.org/'
        - cors_allow_origin: 'https://cantus.org:5733/'

        The mock on Solr simply raises an AssertionError. If you want to use Solr in a test, call
        the :meth:`setUpSolr` method.
        '''
        super(TestHandler, self).setUp()
        self._simple_options_patcher = mock.patch('abbot.simple_handler.options')
        self._simple_options = self._simple_options_patcher.start()
        self._simple_options.drupal_url = None
        self._simple_options.server_name = 'https://cantus.org/'
        self._simple_options.cors_allow_origin = 'https://cantus.org:5733/'

        self._solr_patcher = mock.patch('abbot.util.SOLR')
        self._solr = self._solr_patcher.start()
        self._solr.search = mock.Mock(side_effect=_solr_side_effect)
        self._solr.add = mock.Mock(side_effect=_solr_side_effect)
        self._solr.delete = mock.Mock(side_effect=_solr_side_effect)
        self._solr.more_like_this = mock.Mock(side_effect=_solr_side_effect)
        self._solr.suggest_terms = mock.Mock(side_effect=_solr_side_effect)
        self._solr.commit = mock.Mock(side_effect=_solr_side_effect)
        self._solr.optimize = mock.Mock(side_effect=_solr_side_effect)
        self._solr.extract = mock.Mock(side_effect=_solr_side_effect)

    def setUpSolr(self):
        '''
        Set up a :class:`SolrMock` instance instead of the default (which always raises an
        :exc:`AssertionError`). The :class:`SolrMock` is returned so you can do test-specific setup
        of the "side effect" functions.

        :returns: A fresh, clean :class:`SolrMock` function for your enjoyment while the test lasts.
        '''
        # first remove the default
        self._solr_patcher.stop()
        del self._solr
        # now set up the new one
        self._solr_patcher = mock.patch('abbot.util.SOLR', new=SolrMock)
        self._solr = self._solr_patcher.start()
        SolrMock.__init__(self._solr)  # apparently mock.patch() won't call __init__() for us
        return self._solr

    def tearDown(self):
        '''
        Remove the mock from the global "options" modules.
        '''
        self._simple_options_patcher.stop()
        self._solr_patcher.stop()
        super(TestHandler, self).tearDown()


class SolrMethodSideEffect(object):
    '''
    The "side effect" of a mock on a ``pysolr-tornado`` instance method.

    This class is very strict, intended to survive only a single test, and it tries to make sure you
    don't misconfigure it.

    Instantiate it, add values, call the class. You cannot add values after you call the class,
    which is a sign you should be using more than one test.

    Only the first argument to :meth:`__call__` is used, and the rest are discarded. When you call
    the class, all the "added" keys are iterated and, if the "key" is "in" the first argument, then
    the associated "value" becomes part of what's returned. Do be careful about your expectations
    here: ``id:1 AND id:2``, ``id:1 OR id:2``, and ``id:1 NOT id:2`` all return the same because
    there is no intelligence involved---just an "in" test!

    .. note:: Because the follwing examples produce Tornado :class:`Future` objects, they must be
        used with the ``yield`` keyword. Therefore they must be used within a function, so the
        :class:`SolrMethodSideEffect` (exactly like ``pysolr-tornado``) cannot be experimented with
        arbitrarily.

    .. note:: Once yielded, the functions actually return a :class:`pysolrtornado.Results` object.

    **Example 1**

    >>> se = SolrMethodSideEffect()
    >>> se.add('id:1', {'id': '1'})
    >>> se.add('id:2', {'id': '2'})
    >>> yield se('id:1').docs
    [{'id': '1'}]
    >>> yield se('id:2').docs
    [{'id': '2'}]
    >>> yield se('id:1 OR id:2').docs
    [{'id': '1'}, {'id': '2'}]
    >>> yield se('type:chant AND id:1').docs
    [{'id': '1'}]
    >>> yield se('type:chant AND id:3').docs
    []

    **Example 2**

    You can arrange for multiple records to be returned for a single "key."

    >>> se = SolrMethodSideEffect()
    >>> se.add('*', {'id': '1'})
    >>> se.add('*', {'id': '2'})
    >>> yield se('*').docs
    [{'id': '1'}, {'id': '2'}]

    **Counter Example 1**

    The :meth:`add` method checks the types of its arguments.

    >>> se = SolrMethodSideEffect()
    >>> yield se.add(4, {'id': '4'}).docs
    (raises TypeError because 4 is not a string)
    >>> yield se.add('id:4', 'broccoli').docs
    (raises TypeError because 'broccoli' is not a dict)

    **Counter Example 2**

    The :meth:`add` method cannot be called after you call the class.

    >>> se = SolrMethodSideEffect()
    >>> se.add('1', {'id': '1'})
    >>> yield se('1').docs
    [{'id': '1'}]
    >>> se.add('2', {'id': '2'})
    (raises RuntimeError because you already called the class)
    '''

    def __init__(self):
        "Initialize an empty :class:`SolrMethodSideEffect`."
        self._we_were_called = False
        self._records = {}

    def add(self, key, value):
        '''
        Add a key/value pair to the method.

        :param str key: If this is "in" the first argument to :meth:`__call__`, then ``value`` will
            be part of that method's return value.
        :param dict key: This will be returned by :meth:`__call__` when appropriate.
        :returns: ``None``
        :raises: :exc:`TypeError` when ``key`` or ``value`` are not the proper type.
        :raises: :exc:`RuntimeError` if the class has already been called.

        .. note:: If they "key" has already been added to this mock, the new ``value`` and all
            previous ``value`` are returned.
        '''
        if self._we_were_called:
            raise RuntimeError('You cannot call add() after calling the class.')
        if not isinstance(key, str):
            raise TypeError('The first argument must be a string.')
        if not isinstance(value, dict):
            raise TypeError('The second argument must be a dict.')

        if key in self._records:
            self._records[key].append(value)
        else:
            self._records[key] = [value]

    def __call__(self, query, *args, **kwargs):
        '''
        Check all the "keys" added to this class. If the key is "in" ``query``, the associated
        ``value`` will be part of the list returned by this function.

        :param str query: A query string to check against "added" keys.
        :param any args: Ignored.
        :param any kwargs: Ignored.
        :returns: The associated "value" dicts.
        :rtype: list of dict
        '''
        self._we_were_called = True

        post = []
        for key in self._records.keys():
            if key in query:
                post.extend(self._records[key])

        return make_future(make_results(post))


class SolrMock(object):
    '''
    A mock for a ``pysolr-tornado`` instance.

    This class creates a Mock for each of the ``pysolr-tornado`` public API methods, along with a
    new "side effect" instance of the :class:`SolrMethodSideEffect`.

    The mocked methods are:

    - :meth:`search`
    - :meth:`add`
    - :meth:`delete`
    - :meth:`more_like_this`
    - :meth:`suggest_terms`
    - :meth:`commit`
    - :meth:`optimize`
    - :meth:`extract`

    Access the associated "side effect" by adding ``_se`` to the method name. For example, the
    :meth:`search` "side effect" is attached to :attr:`search_se`.
    '''

    def __init__(self):
        "Initialize all the mock methods on a :class:`SolrMock` instance."
        self.search_se = SolrMethodSideEffect()
        self.add_se = SolrMethodSideEffect()
        self.delete_se = SolrMethodSideEffect()
        self.more_like_this_se = SolrMethodSideEffect()
        self.suggest_terms_se = SolrMethodSideEffect()
        self.commit_se = SolrMethodSideEffect()
        self.optimize_se = SolrMethodSideEffect()
        self.extract_se = SolrMethodSideEffect()
        #
        self.search = mock.Mock(side_effect=self.search_se)
        self.add = mock.Mock(side_effect=self.add_se)
        self.delete = mock.Mock(side_effect=self.delete_se)
        self.more_like_this = mock.Mock(side_effect=self.more_like_this_se)
        self.suggest_terms = mock.Mock(side_effect=self.suggest_terms_se)
        self.commit = mock.Mock(side_effect=self.commit_se)
        self.optimize = mock.Mock(side_effect=self.optimize_se)
        self.extract = mock.Mock(side_effect=self.extract_se)

    def __call__(self, *args, **kwargs):
        raise AssertionError('There is no reason to call a pysolr-tornado instance directly...')
