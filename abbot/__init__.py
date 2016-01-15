__all__ = ['complex_handler', 'handlers', 'simple_handler', 'systemd_http_server', 'util']
__version__ = '0.4.10'
__cantus_version__ = '0.2.3'


# When importing Abbot during the installation, Tornado won't be installed yet, and we also don't
# want to bother importing all the submodules. This shouldn't cause problems later.
try:
    import tornado
    IMPORT_TORNADO = True
except ImportError:  # pragma: no cover
    IMPORT_TORNADO = False


if IMPORT_TORNADO:
    from tornado.options import define
    define('debug', default=True, type=bool, help='whether to start Abbot in a debugging-friendly mode')
    define('about', default=False, type=bool, help='display an message telling about Abbot')
    define('version', default=False, type=bool, help='print Abbot\'s version and of the implemented Cantus API')
    define('licence', default=False, type=bool, help='show licence information')
    define('license', default=False, type=bool, help='show license information')
    define('copyright', default=False, type=bool, help='show copyright information')
    define('options_file', default='', type=str, help='optional path to the server configuration file')

    from abbot import __all__
    # we must retain this import statement to ensure that all modules will be imported with
    # "import abbot" so that all the Tornado options will be definitely registered before use

CANTUS_REQUEST_HEADERS = ('X-Cantus-Per-Page', 'X-Cantus-Page', 'X-Cantus-Include-Resources',
                          'X-Cantus-Sort', 'X-Cantus-No-Xref', 'X-Cantus-Fields',
                          'X-Cantus-Search-Help')
'''
Iterable of the headers that Abbot is interested in reading. Needless to say, Abbot will follow
other headers as applicable---this list determines the value of the
:http:header:`Access-Control-Allow-Headers` header.
'''

CANTUS_RESPONSE_HEADERS = ('X-Cantus-Per-Page', 'X-Cantus-Page', 'X-Cantus-Include-Resources',
                           'X-Cantus-Sort', 'X-Cantus-No-Xref', 'X-Cantus-Fields', 'Server',
                           'X-Cantus-Extra-Fields', 'X-Cantus-Search-Help', 'X-Cantus-Version',
                           'X-Cantus-Total-Results')
'''
Iterable of the headers that Cantus clients are interested in reading. Needless to say, Cantus
clients may be interested in other headers---this list determines the value of the
:http:header:`Access-Control-Expose-Headers` header.
'''
