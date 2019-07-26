# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from .. import TestCase


class BlogTest(TestCase):
    def test_file_structure(self):
        s = self.get_project({
            './one.jpg': '',
            './two.txt': 'some text',
            'other/three.txt': 'third text',
            'post/foo.md': 'post text',
            'page/index.md': 'aux text',
        }, blog=True)
        s.output()

        self.assertTrue(s.output_dir.has_file("one.jpg"))
        self.assertTrue(s.output_dir.has_file("two.txt"))
        self.assertTrue(s.output_dir.child("other").has_file("three.txt"))
        self.assertTrue(s.output_dir.child("post").has_file("index.html"))
        self.assertTrue(s.output_dir.child("page").has_file("index.html"))

