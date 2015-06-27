__all__ = ['handlers', 'util']
__version__ = '0.1.5'
__cantus_version__ = '0.1.4-ext'

from abbott import *

DEBUG = True
'''
Whether the server is in debugging mode. If it is, several things are changed to allow less secure,
more verbose, often slower operation.
'''

CANTUS_REQUEST_HEADERS = ('X-Cantus-Per-Page', 'X-Cantus-Page', 'X-Cantus-Include-Resources',
                          'X-Cantus-Sort', 'X-Cantus-No-Xref', 'X-Cantus-Fields',
                          'X-Cantus-Search-Help')
'''
Iterable of the headers that Abbott is interested in reading. Needless to say, Abbott will follow
other headers as applicable---this list determines the value of the
:http:header:`Access-Control-Allow-Headers` header.
'''

CANTUS_RESPONSE_HEADERS = ('X-Cantus-Per-Page', 'X-Cantus-Page', 'X-Cantus-Include-Resources',
                           'X-Cantus-Sort', 'X-Cantus-No-Xref', 'X-Cantus-Fields',
                           'X-Cantus-Search-Help', 'X-Cantus-Version', 'X-Cantus-Total-Results',
                           'Server')
'''
Iterable of the headers that Cantus clients are interested in reading. Needless to say, Cantus
clients may be interested in other headers---this list determines the value of the
:http:header:`Access-Control-Expose-Headers` header.
'''
