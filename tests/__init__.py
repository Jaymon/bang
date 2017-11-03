# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import unittest
import os
import codecs
import sys
import json
import re
import warnings

import testdata

from bang.generator import Post, Site
from bang.path import Directory
from bang import skeleton
from bang.__main__ import configure_logging
from bang.event import event


# "" to turn on all logging for the tests
configure_logging("")
#configure_logging("DI")


def deprecated(func):
    def wrapped(*args, **kwargs):
        # https://wiki.python.org/moin/PythonDecoratorLibrary#Generating_Deprecation_Warnings
        # http://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
        warnings.warn_explicit(
            "deprecated function {}".format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )

        return func(*args, **kwargs)
    return wrapped


@deprecated
def get_body(filepath):
    return TestCase.get_body(filepath)


@deprecated
def get_dirs(input_files):
    return TestCase.get_dirs(input_files)


@deprecated
def get_posts(post_files):
    return TestCase.get_posts(post_files)


@deprecated
def get_post(post_files, **kwargs):
    for k in post_files:
        if k.endswith(".md"): break
    post_file = post_files.pop(k)
    return TestCase.get_post(post_file, post_files, **kwargs)


class TestCase(unittest.TestCase):

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

        testdata.create_files(d, tmpdir=str(project_dir))
        return project_dir, output_dir

    @classmethod
    def get_site(cls, input_files):
        di = {
            'bangfile.py': [
                "from bang import event",
                "@event('config')",
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
            if "/" in basename:
                fp = os.path.join('input', basename)
            else:
                name = testdata.get_ascii(16)
                fp = os.path.join('input', name, basename)
            di[fp] = file_contents

        project_dir, output_dir = cls.get_dirs(di)

        s = Site(project_dir, output_dir)
        return s

    @classmethod
    def get_posts(cls, post_files):
        s = cls.get_site(post_files)
        s.compile()
        return s.posts if len(s.posts) else s.auxs

    @classmethod
    def get_count_posts(cls, count):
        post_files = {}
        for x in range(count):
            name = testdata.get_ascii(8)
            post_files["{}.md".format(name)] = testdata.get_words()

        s = cls.get_site(post_files)
        s.compile()
        return s.posts if len(s.posts) else s.auxs

    @classmethod
    def get_post(cls, post_file, post_files=None):
        if not post_files:
            post_files = {}

        name = "{}.md".format(testdata.get_ascii(8))
        post_files[name] = post_file

        posts = cls.get_posts(post_files)
        return posts.first_post

    @classmethod
    def get_body(cls, filepath):
        v = u''
        with codecs.open(filepath, 'r+', 'utf-8') as fp:
            v = fp.read()
        return v

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

