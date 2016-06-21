'''
Options Configuration File

This file is part of the "Abbot" Web server for the Cantus API.
Abbot Copyright (C) 2015, 2016 Christopher Antila
'''

# The octothorpe character ("hashtag") begins a comment. Every other line is a possible
# configuration option for Abbot. The file is parsed as Python.


## General ----------------------------------------------------------------------------------------

# "debug" starts the server in a debugging-friendly mode (with more logging information). Because
# this exposes potentially sensitive information to remote clients, you should leave it False in
# deployment.
debug = False


## URLs -------------------------------------------------------------------------------------------

# "hostname" is the fully-qualified domain name as appropriate for links on Abbot itself.
hostname = 'localhost'

# "port" is the port on which Abbot should operate
port = 8888

# The URL where Solr will be found. This must include the full path to the collection to query.
# solr_url = 'http://localhost:8983/solr/collection1/'


## TLS --------------------------------------------------------------------------------------------

# these will cause an error unless you generate the certfile and keyfile first!
certfile = 'tls_test/servercert.pem'
keyfile = 'tls_test/serverkey.pem'
# default cipherlist from Mozilla, "intermediate" settings in April 2016:
# https://mozilla.github.io/server-side-tls/ssl-config-generator/
ciphers = 'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS'


## Cross-Origin Resource Sharing (CORS) -----------------------------------------------------------

# "cors_allow_origin" includes all acceptable values of the Access-Control-Allow-Origin response
# header. The value is always a string, but the string may be a space-separated list of values. For
# example, the following value allows CORS reqeusts from both vitrail.ca and vitrail.de:
#     cors_allow_origin = 'https://vitrail.ca https://vitrail.de'
# If this option is set to None, none of the CORS response headers will be used.
cors_allow_origin = None


## Drupal -----------------------------------------------------------------------------------------

# "drupal_url" is an optional path to a Drupal installation of the Cantus database. Abbot assumes
# that the "id" stored in Solr was exported from that Drupal installation.
# Example:
#    drupal_url = 'http://cantus2.uwaterloo.ca/'
drupal_url = None


## Logging ----------------------------------------------------------------------------------------

# Level of messages to write to the log (debug, info, warning, error, none).
if debug:
    logging = 'debug'
else:
    logging = 'warning'

# send log output to stderr (colourized if possible). This is the default if "log_file_prefix" is
# not configured.
#log_to_stderr = True

# Note that Abbot replaces Tornado's default log "handler" with a connection to systemd-journal
# via the "systemdream" library. This means the other default Tornado log options are ignored.
