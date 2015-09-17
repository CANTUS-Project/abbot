#
# NOTE: I copied this file verbatim from the link given below. The original file has no copyright
#       information, but the "setup.py" file in the same repository says "GPLv3," so I'm quite sure
#       it's compatible with Abbot in that regard. However, any modifications should be published
#       separately from this repository, just in case.
#       -- Christopher Antila
#
# https://github.com/paradoxxxzero/tornado-systemd/blob/674ee6976cbe884239c7b5263c9f43f9d223cfab/tornado_systemd/__init__.py

import os
import socket
from tornado.tcpserver import TCPServer
from tornado.httpserver import HTTPServer

__version__ = '1.0.1'

SYSTEMD_SOCKET_FD = 3  # Magic number !


class SystemdMixin(object):
    @property
    def systemd(self):
        return os.environ.get('LISTEN_PID', None) == str(os.getpid())

    def listen(self, port, address='', backlog=128, family=None, type=None):
        if self.systemd:
            self.request_callback.systemd = True
            # Systemd activated socket
            family = family or (
                socket.AF_INET6 if socket.has_ipv6 else socket.AF_INET)
            type = type or socket.SOCK_STREAM
            sck = socket.fromfd(SYSTEMD_SOCKET_FD, family, type)
            self.add_socket(sck)
            sck.setblocking(0)
            sck.listen(128)
        else:
            self.request_callback.systemd = False
            super(SystemdMixin, self).listen(port, address)


class SystemdTCPServer(SystemdMixin, TCPServer):
    pass


class SystemdHTTPServer(SystemdMixin, HTTPServer):
    pass
