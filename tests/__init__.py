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

from bang.generator import Post, Site, Template
from bang.path import Directory, ProjectDirectory
from bang import skeleton
from bang import config
from bang.__main__ import configure_logging


# "" to turn on all logging for the tests
configure_logging("DI")


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
    name, post_file = post_files.popitem()
    return TestCase.get_post(post_file, post_files, **kwargs)


class TestCase(unittest.TestCase):

    @classmethod
    def get_site(cls, input_files):
        # clear the environment
        for k, v in os.environ.items():
            if k.startswith('BANG_'):
                del os.environ[k]
        sys.modules.pop("bangfile_module", None)

        di = {
            'bangfile.py': [
                "host = 'example.com'",
                "name = 'example site'",
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

        project_dir, output_dir = get_dirs(di)

        s = Site(project_dir, output_dir)
        return s

    @classmethod
    def get_post(cls, post_file, post_files=None):
        if not post_files:
            post_files = {}

        name = "{}.py".format(testdata.get_ascii(8))
        post_files[name] = post_file

        posts = cls.get_posts(*args, **kwargs)
        return posts.first_post

    @classmethod
    def get_posts(cls, post_files):
        s = cls.get_site(post_files)
        s.compile()
        return s.posts if len(s.posts) else s.auxs

    @classmethod
    def get_body(cls, filepath):
        v = u''
        with codecs.open(filepath, 'r+', 'utf-8') as fp:
            v = fp.read()
        return v

    @classmethod
    def get_dirs(cls, input_files):
        # TODO -- switch these to use the skeleton templates
        d = {
            'template/aux.html': "{{ aux.title }}\n{{ aux.html }}\n",
            'template/post.html': "{{ post.title }}\n{{ post.html }}\n{{ post.modified.strftime('%Y-%m-%d') }}\n",
            'template/posts.html': "\n".join([
                "{% for post in posts.reverse(10) %}",
                "{% include 'post.html' %}",
                "<hr>",
                "{% endfor %}",
                "",
            ])
        }
        d.update(input_files)

        output_dir = Directory(testdata.create_dir())
        project_dir = ProjectDirectory(testdata.create_dir())

        testdata.create_files(d, tmpdir=str(project_dir))
        return project_dir, output_dir

