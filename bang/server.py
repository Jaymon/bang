# stdlib
import os
import time
import posixpath
import urllib
import SocketServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

# first party
from . import echo


class DirTCPServer(SocketServer.TCPServer, object):
    """
    Subclass of TCPServer that sets serv_dir
    """
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, serv_dir=os.getcwd()):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.serv_dir = serv_dir


class Server(DirTCPServer):
    """
    Serve files in a specified directory on a specified port
    """
    def __init__(self, serv_dir, port):
        # Change cwd and setup http server
        super(Server, self).__init__(
            ("", port),
            RequestHandler,
            bind_and_activate=False,
            serv_dir=serv_dir
        )

        echo.out("server started on port {} and dir {}", port, serv_dir)

        # Prevent 'cannot bind to address' errors on restart
        # Manually bind, to support allow_reuse_address
        self.allow_reuse_address = True
        self.server_bind()
        self.server_activate()


class RequestHandler(SimpleHTTPRequestHandler):
    """
    Subclass of SimpleHTTPRequestHandler that servers from
    server.serv_dir rather than os.getcwd() 
    """
    def translate_path(self, url_path):
        """
        Translate a /-separated PATH to the local filename syntax.
        """

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

        echo.out("{} -> {}", url_path, path)
        return path

