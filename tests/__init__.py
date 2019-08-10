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
    def get_dirs(cls, project_files=None):
        output_dir = Directory(testdata.create_dir())
        project_dir = Directory(testdata.create_dir())

        if project_files:
            testdata.create_files(project_files, tmpdir=String(project_dir))
        return project_dir, output_dir

    @classmethod
    def get_project(cls, input_files=None, project_files=None, bangfile=None):
        input_files = input_files or {}
        project_files = project_files or {}

        # compile all the bangfile lines
        bangfile_lines = [
            "from bang import event",
            "",
        ]

        if bangfile:
            if isinstance(bangfile, basestring):
                bangfile_lines.append(bangfile)
            else:
                bangfile_lines.extend(bangfile)

        bangfile_lines.extend([
            "",
            "@event('configure')",
            "def global_config(event_name, config):",
            "    config.host = 'example.com'",
            "    config.name = 'example site'",
            ""
        ])

        project_files.setdefault('bangfile.py', bangfile_lines)

        # replace any project files if they are present
        for rp in project_files.keys():
            if rp in input_files:
                project_files[rp] = input_files.pop(rp)

        for basename, file_contents in input_files.items():
            if basename.startswith("input/"):
                fp = basename

            elif basename.startswith("./"):
                fp = basename.replace("./", "input/")

            else:
                fp = "/".join(['input', basename])

#             elif "/" in basename:
#                 fp = os.path.join('input', basename)
#             else:
#                 name = testdata.get_ascii(16)
#                 fp = os.path.join('input', name, basename)
            project_files[fp] = file_contents

        project_dir, output_dir = cls.get_dirs(project_files)
        p = Project(project_dir, output_dir)
        return p

    @classmethod
    def get_pages(cls, page_files):
        p = cls.get_project(page_files)
        p.compile()
        return p.types["page"]

    @classmethod
    def get_count_pages(cls, count):
        page_files = {}
        for x in range(count):
            name = testdata.get_ascii(8)
            page_files["{}/index.md".format(name)] = testdata.get_words()

        return cls.get_pages(page_files)

    @classmethod
    def get_page(cls, page_file="", page_files=None):
        if not page_file:
            page_file = [
                "# title text",
                "",
                "body text",
            ]

        page_files = page_files or {}

        if isinstance(page_file, dict):
            page_files.update(page_file)

        else:
            name = "{}/index.md".format(testdata.get_ascii(8))
            page_files[name] = page_file

        return cls.get_pages(page_files).first_page

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

