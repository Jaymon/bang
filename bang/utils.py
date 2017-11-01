# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
from HTMLParser import HTMLParser
import os
import fnmatch

from jinja2 import Environment, FileSystemLoader


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


class Template(object):
    """Thin wrapper around Jinja functionality that handles templating things

    http://jinja.pocoo.org/docs/dev/
    """
    @property
    def templates(self):
        templates = {}
        for f in fnmatch.filter(os.listdir(str(self.template_dir)), '*.html'):
            filename, fileext = os.path.splitext(f)
            templates[filename] = f
        return templates

    def __init__(self, template_dir):
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            #extensions=['jinja2.ext.with_'] # http://jinja.pocoo.org/docs/dev/templates/#with-statement
        )

    def has(self, template_name):
        return template_name in self.templates

    def output(self, template_name, filepath, **kwargs):
        tmpl = self.env.get_template("{}.html".format(template_name))
        return tmpl.stream(**kwargs).dump(filepath, encoding='utf-8')


