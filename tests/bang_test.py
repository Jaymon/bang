# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import json
import re

import testdata

from bang.compat import *
from bang.path import Directory, File
from bang import skeleton
from bang import config
from . import TestCase


class ProjectTest(TestCase):
    def test_no_bangfile_host(self):
        name = testdata.get_ascii(16)
        ps = self.get_pages({
            '{}/index.md'.format(name): "\n".join([
                "hi"
            ]),
            'bangfile.py': ""
        })

        self.assertRegexpMatches(ps.first_page.url, "^/{}$".format(name))

    def test_single_document(self):
        p = self.get_page({
            'index.md': 'aux text',
            'aux.jpg': '',
        })
        p.output()

        self.assertTrue(p.output_dir.has_file("index.html"))
        self.assertTrue(p.output_dir.has_file("aux.jpg"))

    def test_file_structure(self):
        s = self.get_project({
            './one.jpg': '',
            './two.txt': 'some text',
            'other/three.txt': 'third text',
            'aux/index.md': 'aux text',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("one.jpg"))
        self.assertTrue(s.output_dir.has_file("two.txt"))
        self.assertTrue(s.output_dir.child("other").has_file("three.txt"))
        self.assertTrue(s.output_dir.child("aux").has_file("index.html"))

    def test_unicode_output(self):
        #p = self.get_page({'aux/index.md': testdata.get_unicode_words()})
        p = self.get_page(testdata.get_unicode_words())
        p.output()
        self.assertTrue(p.output_dir.has_file('index.html'))

    def test_drafts(self):
        s = self.get_project({
            '_draft/index.md': testdata.get_words(),
            'notdraft/_index.md': testdata.get_words(),
            'notdraft/foo.jpg': "",
        })
        s.output()

        self.assertFalse(s.output_dir.has_file('_draft', 'index.html'))
        self.assertFalse(s.output_dir.has_file('notdraft', 'index.html'))
        self.assertFalse(s.output_dir.has_file('notdraft', '_index.md'))
        self.assertTrue(s.output_dir.has_file('notdraft', 'foo.jpg'))
        self.assertEqual(0, len(s.get_type("page")))

    def test_private(self):
        s = self.get_project({
            '_foo/index.md': testdata.get_unicode_words(),
            '_foo/fake.jpg': "",
            '_bar/other/something.jpg': "",
        })
        s.output()

        self.assertEqual([], s.get_type("page"))
        self.assertEqual(1, len(s.get_type("other")))

    def test_regex(self):
        s = self.get_project({
        #project_dir, output_dir = get_dirs({
            'foo/index.md': testdata.get_unicode_words(),
            'foo2/index.md': testdata.get_unicode_words(),
            'bar/index.md': testdata.get_unicode_words(),
            'bar/fake.jpg': "",
        })

        #s = Site(project_dir, output_dir)

        s.compile()
        ps = list(s.get_type("page").filter(r"bar"))
        self.assertEqual(1, len(ps))

        ps = list(s.get_type("page").filter(r"foo"))
        self.assertEqual(2, len(ps))

        ps = list(s.get_type("page").filter(r""))
        self.assertEqual(3, len(ps))

        ps = list(s.get_type("page").filter(None))
        self.assertEqual(3, len(ps))

        ps = list(s.get_type("page").filter())
        self.assertEqual(3, len(ps))


class SkeletonTest(TestCase):
    def test_generate(self):
        project_dir = Directory(testdata.create_dir())
        s = skeleton.Skeleton(project_dir)
        s.output()

        for file_dict in skeleton.file_skeleton:
            d = project_dir / file_dict['dir']
            self.assertTrue(d.exists())
            self.assertTrue(os.path.isfile(os.path.join(str(d), file_dict['basename'])))


