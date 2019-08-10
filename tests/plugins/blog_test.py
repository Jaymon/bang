# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from .. import TestCase


class BlogTest(TestCase):
    @classmethod
    def get_project(cls, input_files=None, project_files=None, bangfile=None):
        bangfile = bangfile or []
        bangfile.append(
            "from bang.plugins import blog"
        )
        return super(BlogTest, cls).get_project(
            input_files,
            project_files,
            bangfile=bangfile
        )

    @classmethod
    def get_posts(cls, post_files):
        p = cls.get_project(post_files, blog=True)
        p.compile()
        return p.types["post"]

    @classmethod
    def get_count_posts(cls, count):
        post_files = {}
        for x in range(count):
            name = testdata.get_ascii(8)
            post_files["{}/{}.md".format(name, testdata.get_ascii_words(4))] = testdata.get_words()

        return cls.get_posts(post_files)

    @classmethod
    def get_post(cls, post_file, post_files=None):
        post_file = post_file or {}

        if isinstance(post_file, dict):
            #for k in post_file:
            #    if k.endswith(".md"): break

            post_files = post_file
            #post_file = post_files.pop(k)

        else:
            name = "{}/{}.md".format(testdata.get_ascii(8), testdata.get_ascii_words(4))
            post_files[name] = post_file

        return cls.get_posts(post_files).first_page

    def test_file_structure(self):
        s = self.get_project({
            './one.jpg': '',
            './two.txt': 'some text',
            'other/three.txt': 'third text',
            'post/foo.md': 'post text',
            'page/index.md': 'aux text',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("one.jpg"))
        self.assertTrue(s.output_dir.has_file("two.txt"))
        self.assertTrue(s.output_dir.child("other").has_file("three.txt"))
        self.assertTrue(s.output_dir.child("post").has_file("index.html"))
        self.assertTrue(s.output_dir.child("page").has_file("index.html"))

