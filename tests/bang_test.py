# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import json
import re

import testdata

from bang.compat import *
from bang.path import Directory
from bang import skeleton
from bang import config
from . import TestCase


class ProjectTest(TestCase):
    def test_single_document(self):
        s = self.get_project({
            'index.md': 'aux text',
            'aux.jpg': '',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("index.html"))
        self.assertTrue(s.output_dir.has_file("aux.jpg"))

    def test_file_structure(self):
        s = self.get_project({
            './one.jpg': '',
            './two.txt': 'some text',
            'other/three.txt': 'third text',
            'post/foo.md': 'post text',
            'aux/index.md': 'aux text',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("one.jpg"))
        self.assertTrue(s.output_dir.has_file("two.txt"))
        self.assertTrue(s.output_dir.child("other").has_file("three.txt"))
        self.assertTrue(s.output_dir.child("post").has_file("index.html"))
        self.assertTrue(s.output_dir.child("aux").has_file("index.html"))

    def test_unicode_output(self):
        s = self.get_project({
        #project_dir, output_dir = get_dirs({
            'aux/index.md': testdata.get_unicode_words(),
        })

        #s = Site(project_dir, output_dir)
        s.output()

        self.assertTrue(os.path.isfile(os.path.join(String(s.output_dir), 'aux', 'index.html')))

    def test_drafts(self):
        s = self.get_project({
        #project_dir, output_dir = get_dirs({
            '_draft/foo.md': testdata.get_words(),
            'notdraft/_bar.md': testdata.get_words(),
        })

        #s = Site(project_dir, output_dir)
        s.output()

        self.assertFalse(os.path.isfile(os.path.join(String(s.output_dir), '_draft', 'index.html')))
        self.assertFalse(os.path.isfile(os.path.join(String(s.output_dir), 'notdraft', 'index.html')))
        self.assertEqual(0, len(s.posts))

    def test_regex_compile(self):
        s = self.get_project({
        #project_dir, output_dir = get_dirs({
            'foo/post1.md': testdata.get_unicode_words(),
            'foo2/post2.md': testdata.get_unicode_words(),
            'bar/post3.md': testdata.get_unicode_words(),
            'bar/fake.jpg': "",
        })

        #s = Site(project_dir, output_dir)

        s.output(r"bar")
        count = 0
        for p in s.posts:
            if p.output_dir.exists():
                count += 1
        self.assertEqual(1, count)

        s.output(r"bar")
        count = 0
        for p in s.posts:
            if p.output_dir.exists():
                count += 1
        self.assertEqual(1, count)

        s.output()
        count = 0
        for p in s.posts:
            if p.output_dir.exists():
                count += 1
        self.assertEqual(3, count)

    def test_private_post(self):
        s = self.get_project({
        #project_dir, output_dir = get_dirs({
            '_foo/post1.md': testdata.get_unicode_words(),
            '_foo/fake.jpg': "",
            '_bar/other/something.jpg': "",
        })

        #s = Site(project_dir, output_dir)

        s.output()
        self.assertIsNone(s.posts.first_page)
        self.assertEqual(1, len(s.others))


class SkeletonTest(TestCase):
    def test_generate(self):
        project_dir = Directory(testdata.create_dir())
        s = skeleton.Skeleton(project_dir)
        s.output()

        for file_dict in skeleton.file_skeleton:
            d = project_dir / file_dict['dir']
            self.assertTrue(d.exists())
            self.assertTrue(os.path.isfile(os.path.join(str(d), file_dict['basename'])))


