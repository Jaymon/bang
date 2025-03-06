# -*- coding: utf-8 -*-
import unittest
import os
import codecs
import sys
import json
import re

import testdata
from datatypes import Path

from bang.compat import *
from bang.decorators import deprecated
from bang import Project
from bang.__main__ import configure_logging
from bang.event import event


# "" to turn on all logging for the tests
configure_logging("")
#configure_logging("DI")


class TestCase(testdata.TestCase):

    plugins = []

    @classmethod
    def create_config(cls, input_files=None, **kwargs):
        p = cls.get_project(input_files)
        if kwargs:
            for k, v in kwargs.items():
                p.config.set(k, v)
        return p.config
    get_config = create_config

    @classmethod
    def get_dirs(cls, project_files=None):
        project_dir = testdata.create_dir()
        output_dir = testdata.create_dir("output", tmpdir=project_dir)

        if project_files:
            for fp, contents in Path.normpaths(project_files):
                m = re.search(r"\.(jpg|gif|png)$", fp[-1], re.I)
                if m:
                    testdata.create_image(
                        image_type=m.group(1),
                        path=os.path.join(*fp),
                        tmpdir=project_dir
                    )

                else:
                    testdata.create_file(
                        data=contents, 
                        path=fp,
                        tmpdir=project_dir
                    )

        return project_dir, output_dir

    @classmethod
    def get_bangfile_lines(cls, *lines):
        bangfile_lines = []
        for bangfile in lines:
            if bangfile:
                if isinstance(bangfile, basestring):
                    bangfile = [bangfile]

                bangfile_lines.extend(bangfile)

        plugins = cls.plugins
        if isinstance(plugins, basestring):
            plugins = [plugins]

        for plugin in plugins:
            bangfile_lines.append("from bang.plugins import {}".format(plugin))

        return bangfile_lines

    @classmethod
    def get_project_files(
        cls,
        input_files=None,
        project_files=None,
        bangfile=None
    ):
        input_files = input_files or {}
        project_files = project_files or {}

        # compile all the bangfile lines
        bangfile_lines = [
            "from bang import event",
            "",
        ]

        bangfile_lines.extend(cls.get_bangfile_lines(bangfile))

        bangfile_lines.extend([
            "",
            "@event('configure.project')",
            "def configure_project(event):",
            "    config = event.config",
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

            project_files[fp] = file_contents

        return project_files

    @classmethod
    def get_project(cls, input_files=None, project_files=None, bangfile=None):
        project_files = cls.get_project_files(
            input_files,
            project_files,
            bangfile
        )
        project_dir, output_dir = cls.get_dirs(project_files)
        p = Project(project_dir, output_dir)
        return p

    @classmethod
    def get_pages(cls, input_files, **kwargs):
        p = cls.get_project(input_files, **kwargs)
        p.compile()
        return p.types["page"]

    @classmethod
    def get_count_pages(cls, count, **kwargs):
        input_files = {}
        for x in range(count):
            prefix = testdata.get_ascii(8)
            input_files[f"{prefix}/page.md"] = testdata.get_words()

        return cls.get_pages(input_files, **kwargs)

    @classmethod
    def get_page(cls, input_file="", input_files=None, **kwargs):
        input_files = input_files or {}
        prefix = kwargs.pop("prefix", testdata.get_ascii(8))

        if isinstance(input_file, dict):
            input_files[prefix] = input_file

        else:
            if not input_file:
                input_file = [
                    "# title text",
                    "",
                    "body text",
                ]

            input_files[f"{prefix}/page.md"] = input_file

        return cls.get_pages(input_files, **kwargs)[0]

#         else:
#             prefix = testdata.get_ascii(8)
#             name = "{}/page.md".format(prefix)
# 
#             #page_files[name] = page_file
#             pf = {
#                 prefix: page_files,
#                 name: page_file
#             }
#             page_files = pf
# 
#         return cls.get_pages(page_files, bangfile=bangfile)[0]

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

    @classmethod
    def get_type(cls, type_class, relpath):
        project_input_dir = testdata.create_dir()
        input_file = testdata.create_file(
            path=relpath,
            tmpdir=project_input_dir
        )

        project_output_dir = testdata.create_dir()
        output_file = testdata.get_file(
            path=relpath,
            tmpdir=project_output_dir
        )
        config = testdata.mock(
            input_dir=project_input_dir,
            output_dir=project_output_dir
        )

        return type_class(
            input_file,
            output_file.parent,
            config
        )

    def setUp(self):
        # clear the environment
        for k, v in os.environ.items():
            if k.startswith('BANG_'):
                del os.environ[k]

        # clear any loaded bangfiles
        for k in list(sys.modules.keys()):
            if k.startswith("bangfile_"):
                # we don't want any rogue bangfiles hanging around in memory,
                # just in case
                sys.modules.pop(k, None)

            elif k.startswith("bang.plugins"):
                # plugins usually bind to events, so we clear those so they
                # can be rebound
                sys.modules.pop(k, None)

            elif k.startswith("bang.bangfile"):
                # global bangfile 
                sys.modules.pop(k, None)

        # clear singletons
        event.reset()

