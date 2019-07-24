# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
from HTMLParser import HTMLParser
import os


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


class PageIterator(object):
    def __init__(self, config, pagetypes):
        self.config = config
        self.pagetypes = pagetypes

    def __call__(self):
        # for dt_class in conf.dirtypes:
        for pages in self.get_pages():
            for instance in reversed(pages):
                yield instance

    def has(self):
        for pages in self.get_pages():
            if pages:
                return True
        return False

    def get_pages(self):
        for pagetype in self.pagetypes:
            if pagetype.name in self.config.project.pages:
                yield self.config.project.pages[pagetype.name]

