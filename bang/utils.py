# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import re
import time
from collections import defaultdict, Counter

from datatypes import (
    Url,
    HTML,
    Profiler,
)
from datatypes.html import UnlinkedTagTokenizer

from .compat import *


# class Url(String):
#     REGEX = re.compile(r"^(?:https?:\/\/|\/\/)", re.I)
#    """regex to decide if something is a url"""

#     @property
#     def parts(self):
#         o = getattr(self, "_parts", None)
#         if o is None:
#             o = parse.urlsplit(self)
#             self._parts = o
#         return o
# 
#     @property
#     def host(self):
#         return self.parts.netloc
# 
#     @property
#     def path(self):
#         return self.parts.path
# 
#     @property
#     def ext(self):
#         """return the extension of the file, the basename without the fileroot"""
#         return os.path.splitext(self.basename)[1].lstrip(".")
#     extension = ext
# 
#     @property
#     def basename(self):
#         return os.path.basename(self.path)

#     def __new__(cls, base_url, *paths):
#         paths = cls.normalize_paths(*paths)
#         if paths:
#             url = "{}/{}".format(base_url.rstrip("/"), "/".join(paths))
#         else:
#             url = base_url
#         instance = super(Url, cls).__new__(cls, url)
#         return instance
# 
#     @classmethod
#     def normalize_paths(cls, *paths):
#         args = []
#         for ps in paths:
#             if isinstance(ps, basestring):
#                 args.extend(filter(None, ps.split("/")))
#                 #args.append(ps.strip("/"))
#             else:
#                 for p in ps:
#                     args.extend(cls.normalize_paths(p))
#         return args

#     @classmethod
#     def match(cls, url):
#         return True if cls.REGEX.match(url) else False
# 
#     def is_host(self, host):
#         """return true if the url's host matches host"""
#         return self.host and host and (self.host.lower() == host.lower())
# 
#     def is_local(self, config):
#         """return True if is a local url to the project"""
#         ret = False
#         if self.startswith("//"):
#             ret = True
#         elif re.match(r"^/[^/]", self):
#             ret = True
#         elif self.is_host(config.host):
#             ret = True
#         return ret
# 
#     def breadcrumbs(self):
#         """Returns the list of breadcrumbs for path
# 
#         :returns: list, so if path was /foo/bar/che this would return
#             [/foo, /foo/bar, /foo/bar/che]
#         """
#         ret = []
#         path = self.path
#         paths = path.strip("/").split("/")
# 
#         for x in range(1, len(paths) + 1):
#             ret.append("/" + "/".join(paths[0:x]))
# 
#         return ret


class ContextCache(object):
    @property
    def context_name(self):
        return self.config.context_name

    @property
    def context_dict(self):
        return self.d[self.context_name]

    def __init__(self, config):
        self.config = config
        self.d = defaultdict(dict)

    def __getitem__(self, k):
        cd = self.context_dict
        return cd[k]

    def __contains__(self, k):
        cd = self.context_dict
        return k in cd

    def get(self, k, default_val=None):
        if k in self:
            return self[k]
        else:
            return default_val

    def pop(self, k, default_val=None):
        ret = default_val
        if k in self:
            ret = self[k]
            del self[k]
        return ret

    def __setitem__(self, k, v):
        cd = self.context_dict
        cd[k] = v

    def __delitem__(self, k):
        cd = self.context_dict
        del cd[k]

    def items(self):
        cd = self.context_dict
        for k, v in cd.items():
            yield k, v

    def keys(self):
        for k, v in self.items():
            yield k


