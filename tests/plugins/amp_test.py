# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from .. import TestCase


class AmpTest(TestCase):

    @classmethod
    def get_project(cls, input_files=None, project_files=None, bangfile=None):
        bangfile = bangfile or []
        bangfile.append(
            "from bang.plugins import amp"
        )
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
        pout.v(p.input_dir)

        p.config.project.output()
        #amp = p.output_dir.file_contents("amp/index.html")

        return




#         s = self.get_project({
#             './one.jpg': '',
#             './two.txt': 'some text',
#             'other/three.txt': 'third text',
#             'post/foo.md': 'post text',
#             'page/index.md': 'aux text',
#         }, blog=True)
#         s.output()
# 
#         self.assertTrue(s.output_dir.has_file("one.jpg"))
#         self.assertTrue(s.output_dir.has_file("two.txt"))
#         self.assertTrue(s.output_dir.child("other").has_file("three.txt"))
#         self.assertTrue(s.output_dir.child("post").has_file("index.html"))
#         self.assertTrue(s.output_dir.child("page").has_file("index.html"))

