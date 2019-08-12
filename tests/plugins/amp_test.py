# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from .. import TestCase


class AmpTest(TestCase):

    @classmethod
    def get_project(cls, input_files=None, project_files=None, bangfile=None):
        bangfile = bangfile or []
        bangfile.insert(0, "from bang.plugins import amp")
        return super(AmpTest, cls).get_project(
            input_files,
            project_files,
            bangfile=bangfile
        )

    def test_image(self):
        p = self.get_page([
            "![this is the file](foo.jpg)",
            "",
            "bar.png",
            ""
        ])
        testdata.create_jpg("foo.jpg", tmpdir=p.input_dir)
        testdata.create_png("bar.png", tmpdir=p.input_dir)

        p.config.project.output()

        self.assertTrue(p.output_dir.has_directory("amp"))
        self.assertTrue(p.output_dir.has_file("amp", "index.html"))

        amp = p.output_dir.child_directory("amp").file_contents("index.html")
        self.assertTrue("<amp-img" in amp)

        amp = p.output_dir.file_contents("index.html")
        self.assertFalse("<amp-img" in amp)

