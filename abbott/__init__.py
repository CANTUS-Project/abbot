__all__ = ['complex_handler', 'handlers', 'simple_handler', 'util']
__version__ = '0.2.1'
__cantus_version__ = '0.2.0'


from tornado.options import define
define('debug', default=True, type=bool, help='whether to start Abbott in a debugging-friendly mode')
define('about', default=False, type=bool, help='display an message telling about Abbott')
define('version', default=False, type=bool, help='print Abbott\'s version and of the implemented Cantus API')
define('licence', default=False, type=bool, help='show licence information')
define('license', default=False, type=bool, help='show license information')
define('copyright', default=False, type=bool, help='show copyright information')
define('options_file', default='', type=str, help='optional path to the server configuration file')

from abbott import *
# we must retain this import statement to ensure that all modules will be imported with
# "import abbott" so that all the Tornado options will be definitely registered before use

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
