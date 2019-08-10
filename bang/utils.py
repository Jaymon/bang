# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import re

from .compat import *


# http://stackoverflow.com/a/925630/5006
class HTMLStripper(HTMLParser):
    """strip html tags"""
    @classmethod
    def strip_tags(cls, html):
        s = cls()
        s.feed(html)
        return s.get_data()

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class Profile(object):
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exception_type, exception_val, trace):
        self.stop = time.time()
        multiplier = 1000.00
        rnd = 2
        self.elapsed = round(abs(stop - start) * float(multiplier), rnd)
        self.total = "{:.1f} ms".format(self.elapsed)

    def __unicode__(self):
        return self.total

    def __str__(self):
        return ByteString(self.total) if is_py2 else self.total


class Url(String):
    REGEX = re.compile(r"^(?:https?:\/\/|\/\/)", re.I)
    """regex to decide if something is a url"""

    @property
    def parts(self):
        o = getattr(self, "_parts", None)
        if o is None:
            o = parse.urlsplit(self)
            self._parts = o
        return o

    @property
    def host(self):
        return self.parts.hostname

    @property
    def path(self):
        return self.parts.path

    def __new__(cls, base_url, *paths):
        paths = cls.normalize_paths(*paths)
        if paths:
            url = "{}/{}".format(base_url.rstrip("/"), "/".join(paths))
        else:
            url = base_url
        instance = super(Url, cls).__new__(cls, url)
        return instance

    @classmethod
    def normalize_paths(cls, *paths):
        args = []
        for ps in paths:
            if isinstance(ps, basestring):
                args.extend(filter(None, ps.split("/")))
                #args.append(ps.strip("/"))
            else:
                for p in ps:
                    args.extend(cls.normalize_paths(p))
        return args

    @classmethod
    def match(cls, url):
        return True if cls.REGEX.match(url) else False

    def is_host(self, host):
        """return true if the url's host matches host"""
        return self.host.lower() == host.lower()

    def is_local(self, config):
        """return True if is a local url to the project"""
        ret = False
        if self.startswith("//"):
            ret = True
        elif re.match(r"^/[^/]", self):
            ret = True
        elif self.is_host(config.host):
            ret = True
        return ret

