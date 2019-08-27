# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import time
import posixpath
import urllib
import logging

from .compat import *


logger = logging.getLogger(__name__)


class Server(HTTPServer):
    """
    Serve files in a specified directory on a specified port to localhost
    """
    def __init__(self, serv_dir, port):
        if not serv_dir:
            serv_dir = os.getcwd()
        self.serv_dir = serv_dir

        if is_py2:
            HTTPServer.__init__(
                self,
                ("", port),
                RequestHandlerClass=RequestHandler,
            )

        else:
            super(Server, self).__init__(
                ("", port),
                RequestHandlerClass=RequestHandler,
            )

        logger.debug("server started on port {} and dir {}".format(port, serv_dir))


class RequestHandler(SimpleHTTPRequestHandler):
    """
    Subclass of SimpleHTTPRequestHandler that servers from
    server.serv_dir rather than os.getcwd() 
    """
    def translate_path(self, url_path):
        """
        Translate a /-separated PATH to the local filename syntax.
        """

        # TODO This feels like it could be absorbed into utils.Url and
        # path.Directory
        # abandon query parameters
        path = url_path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = self.server.serv_dir
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)

        logger.debug("{} -> {}".format(url_path, path))
        return path

