# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from bang.types import Type

from .. import TestCase


class BlogTest(TestCase):

    plugins = [
        "blog"
    ]

    @classmethod
    def get_posts(cls, post_files):
        p = cls.get_project(post_files)
        p.compile()
        return p.types["post"]

    def test_file_structure(self):
        s = self.get_project({
            './one.jpg': '',
            './two.txt': 'some text',
            'other/three.txt': 'third text',
            'post1/post.md': '# Post 1\n\npost 1 text',
            'post1/page1/page.md': 'page 1 text',
            'page2/page.md': 'page 2 text',
            'page2/post2/post.md': '# Post 2\n\npost 2 text',
            'page3/page.md': 'page 3 text',
            'page4/page.md': 'page 4 text',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("one.jpg"))
        self.assertTrue(s.output_dir.has_file("two.txt"))
        self.assertTrue(s.output_dir.child("other").has_file("three.txt"))
        self.assertTrue(s.output_dir.child("post1").has_file("index.html"))
        self.assertTrue(s.output_dir.child("post1", "page1").has_file("index.html"))
        self.assertTrue(s.output_dir.child("page2").has_file("index.html"))
        self.assertTrue(s.output_dir.child("page2", "post2").has_file("index.html"))

        self.assertEqual(2, s.get_type("post"))
        self.assertEqual(3, s.get_type("other"))
        self.assertEqual(4, s.get_type("page"))

    def test_config_types(self):
        c = self.get_config()
        for t in c.types:
            self.assertTrue(issubclass(t, Type))

