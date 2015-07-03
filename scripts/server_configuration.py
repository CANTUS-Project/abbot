#
# Options Configuration File
#
# This file is part of the "Abbott" Web server for the Cantus API.
# Abbott Copyright (C) 2015 Christopher Antila

# The octothorpe character ("hashtag") begins a comment. Every other line is a possible
# configuration option for Abbott. The file is parsed as Python.


## General ----------------------------------------------------------------------------------------

# "debug" starts the server in a debugging-friendly mode (with more logging information). Because
# this exposes potentially sensitive information to remote clients, you should leave it False in
# deployment.
debug = False


## URLs -------------------------------------------------------------------------------------------

# "scheme" is either "http" or "https" as appropriate for links on Abbott itself.
scheme = 'http'

# "hostname" is the fully-qualified domain name as appropriate for links on Abbott itself.
hostname = 'localhost'

# "port" is the port on which Abbott should operate
port = 8888

# "drupal_url" is an optional, specially-formatted path to a Drupal installation of the Cantus
# database. The URL should have "{id}" in it where the "id" of a record should be substituted.
# Abbott assumes that the "id" stored in Solr was exported from that Drupal installation. Example:
#    drupal_url = 'http://cantus2.uwaterloo.ca/node/{id}'
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

# path prefix for log files. Note that if you are running multiple Tornado processes, this must be
# different for each of them (e.g., include the port number)
log_file_prefix = '/var/log/abbott/server.log'

# number of log files to keep
#log_file_num_backups = 10

# "max size of log files before rollover
#log_file_max_size = 100000000
