#
# Options Configuration File
#
# This file is part of the "Abbot" Web server for the Cantus API.
# Abbot Copyright (C) 2015, 2016 Christopher Antila

# The octothorpe character ("hashtag") begins a comment. Every other line is a possible
# configuration option for Abbot. The file is parsed as Python.


## General ----------------------------------------------------------------------------------------

# "debug" starts the server in a debugging-friendly mode (with more logging information). Because
# this exposes potentially sensitive information to remote clients, you should leave it False in
# deployment.
debug = False


## URLs -------------------------------------------------------------------------------------------

# "scheme" is either "http" or "https" as appropriate for links on Abbot itself.
scheme = 'http'

# "hostname" is the fully-qualified domain name as appropriate for links on Abbot itself.
hostname = 'localhost'

# "port" is the port on which Abbot should operate
port = 8888

# The URL where Solr will be found. This must include the full path to the collection to query.
# solr_url = 'http://localhost:8983/solr/collection1/'


## Cross-Origin Resource Sharing (CORS) -----------------------------------------------------------

# "cors_allow_origin" will be the value of the Access-Control-Allow-Origin response header. If this
# is set to None, none of the CORS response headers will be used.
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
