# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import re
import time
from collections import defaultdict, Counter

from .compat import *


class Profile(object):
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exception_type, exception_val, trace):
        self.stop = time.time()
        multiplier = 1000.00
        rnd = 2
        self.elapsed = round(abs(self.stop - self.start) * float(multiplier), rnd)
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
        return self.parts.netloc

    @property
    def path(self):
        return self.parts.path

    @property
    def ext(self):
        """return the extension of the file, the basename without the fileroot"""
        return os.path.splitext(self.basename)[1].lstrip(".")
    extension = ext

    @property
    def basename(self):
        return os.path.basename(self.path)

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
        return self.host and host and (self.host.lower() == host.lower())

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

    def breadcrumbs(self):
        """Returns the list of breadcrumbs for path

        :returns: list, so if path was /foo/bar/che this would return
            [/foo, /foo/bar, /foo/bar/che]
        """
        ret = []
        path = self.path
        paths = path.strip("/").split("/")

        for x in range(1, len(paths) + 1):
            ret.append("/" + "/".join(paths[0:x]))

        return ret


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


class Scanner(object):
    """Python implementation of Obj-c Scanner

    https://github.com/Jaymon/PlusPlus/blob/master/PlusPlus/NSString%2BPlus.m
    """
    def __init__(self, text):
        self.text = text
        self.offset = 0
        self.length = len(self.text)

    def to(self, char):
        """scans and returns string up to char"""
        partial = ""
        while (self.offset < self.length) and (self.text[self.offset] != char):
            partial += self.text[self.offset]
            self.offset += 1

        return partial

    def until(self, char):
        """similar to to() but includes the char"""
        partial = self.to(char)
        if self.offset < self.length:
            partial += self.text[self.offset]
            self.offset += 1
        return partial

    def __nonzero__(self): return self.__bool__() # py <3
    def __bool__(self):
        return self.offset < self.length


class UnlinkedTagTokenizer(object):
    """This will go through an html block of code and return pieces that aren't
    linked (between <a> and </a>), allowing you to mess with the blocks of plain
    text that isn't special in some way"""

    def __init__(self, text):
        self.s = Scanner(text)

    def __iter__(self):
        """returns plain text blocks that aren't in html tags"""
        start_set = set(["<a ", "<pre>", "<pre "])
        stop_set = set(["</a>", "</pre>"])

        s = self.s
        tag = ""
        plain = s.to("<")
        while s:
            yield tag, plain

            tag = s.until(">")
            plain = s.to("<")
            if [st for st in start_set if tag.startswith(st)]:
            #if tag.startswith("<a"):
                # get rid of </a>, we can't do anything with the plain because it
                # is linked in an <a> already
                #while not tag.endswith("</a>"):
                while len([st for st in stop_set if tag.endswith(st)]) == 0:
                    tag += plain
                    tag += s.until(">")
                    plain = s.to("<")

        # pick up any stragglers
        yield tag, plain


class HTMLStripper(HTMLParser):
    """strip html tags and return plaintext data

    https://docs.python.org/3/library/html.parser.html
    http://stackoverflow.com/a/925630/5006
    """
    @classmethod
    def strip_tags(cls, html, remove_tags=None):
        s = cls(html, remove_tags)
        return s.get_data()

    def __init__(self, html="", remove_tags=None):
        #self.reset()
        if is_py2:
            HTMLParser.__init__(self)
        else:
            super(HTMLStripper, self).__init__()

        self.fed = []
        self.removed = Counter()
        self.remove_tags = set(remove_tags or [])

        if html:
            self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag in self.remove_tags:
            if tag not in self.removed:
                self.removed[tag] = 0

        # really basic css selector support
        for k, v in attrs:
            if k == "class":
                if "{}.{}".format(tag, v) in self.remove_tags:
                    self.removed[tag] = 0

            if k == "id":
                if "{}#{}".format(tag, v) in self.remove_tags:
                    self.removed[tag] = 0

        if tag in self.removed:
            self.removed[tag] += 1

        #pout.b("handle_starttag")
        #pout.v(tag, self.removed)

    def handle_data(self, d):
        #pout.b("handle_data")
        #pout.v(self.removed, d)
        if sum(self.removed.values()) == 0:
            self.fed.append(d)

    def handle_endtag(self, tag):
        if sum(self.removed.values()) > 0:
            if tag in self.removed:
                self.removed[tag] -= 1
                if self.removed[tag] <= 0:
                    del self.removed[tag]

        #pout.b("handle_endtag")
        #pout.v(tag, self.removed)

    def get_data(self):
        return ''.join(self.fed)


class HTML(String):
    def inject_into_head(self, html):
        def callback(m):
            return "{}{}{}".format(m.group(1), html, m.group(0))

        regex = r"(\s*)(</head>)"
        ret = re.sub(regex, callback, self, flags=re.I|re.M)
        return type(self)(ret)

    def inject_into_body(self, html):
        def callback(m):
            return "{}{}{}".format(m.group(1), html, m.group(0))

        regex = r"(\s*)(</body>)"
        ret = re.sub(regex, callback, self, flags=re.I|re.M)
        return type(self)(ret)

    def strip_tags(self, remove_tags=None):
        return HTMLStripper(self, remove_tags=remove_tags).get_data()


