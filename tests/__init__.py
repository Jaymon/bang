# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import unittest
import os
import codecs
import sys
import json
import re

import testdata

from bang.compat import *
from bang.decorators import deprecated
from bang import Project
from bang.path import Directory
from bang import skeleton
from bang.__main__ import configure_logging
from bang.event import event


# "" to turn on all logging for the tests
configure_logging("")
#configure_logging("DI")


class TestCase(testdata.TestCase):

    @classmethod
    def create_config(cls, input_files=None):
        p = cls.get_project(input_files)
        return p.config

    @classmethod
    def get_dirs(cls, input_files):
        # TODO -- switch these to use the skeleton templates
        d = {
            'template/aux.html': "{{ aux.title }}\n{{ aux.html }}\n",
            'template/post.html': "{{ post.title }}\n{{ post.html }}\n{{ post.modified.strftime('%Y-%m-%d') }}\n",
            'template/posts.html': "\n".join([
                "{% for post in posts %}",
                "{% include 'post.html' %}",
                "<hr>",
                "{% endfor %}",
                "",
            ])
        }
        d.update(input_files)

        output_dir = Directory(testdata.create_dir())
        project_dir = Directory(testdata.create_dir())

        testdata.create_files(d, tmpdir=String(project_dir))
        return project_dir, output_dir

    @classmethod
    def get_project(cls, input_files=None):
        input_files = input_files or {}
        di = {
            'bangfile.py': [
                "from bang import event",
                "@event('configure')",
                "def global_config(event_name, config):",
                "    config.host = 'example.com'",
                "    config.name = 'example site'",
                ""
            ]
        }

        # replace any project files if they are present
        for rp in di.keys():
            if rp in input_files:
                di[rp] = input_files.pop(rp)

        for basename, file_contents in input_files.items():
            if basename.startswith("input/"):
                fp = basename
            elif "/" in basename:
                fp = os.path.join('input', basename)
            else:
                name = testdata.get_ascii(16)
                fp = os.path.join('input', name, basename)
            di[fp] = file_contents

        project_dir, output_dir = cls.get_dirs(di)

        p = Project(project_dir, output_dir)
        return p

    @classmethod
    def get_posts(cls, post_files):
        p = cls.get_project(post_files)
        p.compile()
        return p.posts if len(p.posts) else p.auxs

    @classmethod
    def get_count_posts(cls, count):
        post_files = {}
        for x in range(count):
            name = testdata.get_ascii(8)
            post_files["{}.md".format(name)] = testdata.get_words()

        p = cls.get_project(post_files)
        p.compile()
        return p.posts if len(p.posts) else p.auxs

    @classmethod
    def get_post(cls, post_file, post_files=None):
        if not post_files:
            post_files = {}

        if isinstance(post_file, dict):
            #for k in post_file:
            #    if k.endswith(".md"): break

            post_files = post_file
            #post_file = post_files.pop(k)

        else:
            name = "{}.md".format(testdata.get_ascii(8))
            post_files[name] = post_file

        posts = cls.get_posts(post_files)
        return posts.first_page

    @classmethod
    def get_body(cls, filepath):
        v = u''
        with codecs.open(filepath, 'r+', 'utf-8') as fp:
            v = fp.read()
        return v

    @classmethod
    def get_html(cls, body):
        md = Markdown.get_instance()
        html = md.convert(body)
        meta = md.Meta
        html.meta = meta
        return html

    def setUp(self):
        # clear the environment
        for k, v in os.environ.items():
            if k.startswith('BANG_'):
                del os.environ[k]

        # clear any loaded bangfiles
        for k in sys.modules.keys():
            if k.startswith("bangfile_"):
                # we don't want any rogue bangfiles hanging around in memory, just in case
                sys.modules.pop(k, None)

            elif k.startswith("bang.plugins"):
                # plugins usually bind to events, so we clear those so they can
                # be rebound
                sys.modules.pop(k, None)

            elif k.startswith("bang.bangfile"):
                # global bangfile 
                sys.modules.pop(k, None)

        # clear singletons
        event.bound.clear()

