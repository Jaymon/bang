# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import json
import re

import testdata

from bang.compat import *
from bang.path import Dirpath, Filepath
from bang import config
from . import TestCase


class ProjectTest(TestCase):
    def test_is_private_basename(self):
        """makes sure the default private callback works as expected"""
        p = self.get_project()

        self.assertFalse(p.is_private_basename("foo"))
        self.assertTrue(p.is_private_basename("_foo"))
        self.assertTrue(p.is_private_basename(".foo"))
        self.assertTrue(p.is_private_basename(".foo.ext"))
        self.assertTrue(p.is_private_basename("_foo.ext"))

    def test___iter__(self):
        p = self.get_project({
            "foo/page.md": "1",
            "bar/_page.md": "2",
            "bar/_baz/NOTES.txt": "3",
            "_NOTES_2.txt": "4",
            "boo/_che/bam/page.md": "5",
            "boo/page.md": "6",
            "boo/NOTES_3.txt": "7",
        })

        r_count = 0
        r = set(["foo/page.md", "boo/NOTES_3.txt", "boo/page.md"])
        for rp, ip, op in p:
            if not rp.endswith(".css"):
                self.assertTrue(rp in r)
                r_count += 1
        self.assertEqual(len(r), r_count)

    def test_compile(self):
        p = self.get_project({
            "foo/page.md": "1",
            "bar/_page.md": "2",
            "bar/_baz/NOTES.txt": "3",
            "_NOTES_2.txt": "4",
            "boo/_che/bam/page.md": "5",
            "boo/page.md": "6",
            "boo/NOTES_3.txt": "7",
        })

        p.compile()
        self.assertEqual(2, len(p.get_types("page")))
        self.assertEqual(1, len(p.get_types("other")))

    def test_no_bangfile_host(self):
        name = testdata.get_ascii(16)
        ps = self.get_pages({
            f'{name}/page.md': "hi",
            'bangfile.py': ""
        })

        self.assertRegex(ps[0].url, rf"^/{name}/?$")

    def test_single_document(self):
        p = self.get_page('page text')
        p.output()
        self.assertTrue(p.output_dir.has_file("index.html"))

    def test_file_structure(self):
        s = self.get_project({
            'one.jpg': '',
            'two.txt': 'some text',
            'other/three.txt': 'third text',
            'aux/page.md': 'aux text',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("one.jpg"))
        self.assertTrue(s.output_dir.has_file("two.txt"))
        self.assertTrue(s.output_dir.has_file("other", "three.txt"))
        self.assertTrue(s.output_dir.has_file("aux", "index.html"))

    def test_unicode_output(self):
        p = self.get_page(testdata.get_unicode_words())
        p.output()
        self.assertTrue(p.output_dir.has_file('index.html'))

    def test_drafts(self):
        s = self.get_project({
            '_draft/page.md': testdata.get_words(),
            'notdraft/_page.md': testdata.get_words(),
            'notdraft/foo.jpg': "",
        })
        s.output()

        self.assertFalse(s.output_dir.has_file('_draft', 'index.html'))
        self.assertFalse(s.output_dir.has_file('notdraft', 'index.html'))
        self.assertFalse(s.output_dir.has_file('notdraft', '_page.md'))
        self.assertTrue(s.output_dir.has_file('notdraft', 'foo.jpg'))
        self.assertEqual(0, len(s.get_types("page")))

    def test_private(self):
        s = self.get_project({
            '_foo/page.md': testdata.get_unicode_words(),
            '_foo/fake.jpg': "",
            '_bar/other/something.jpg': "",
        })
        s.output()

        self.assertEqual(0, len(s.get_types("page")))
        self.assertEqual(0, len(s.get_types("other")))


class GenerateTest(TestCase):
    def test_generate(self):
        project_dir = testdata.create_dir()

        r = testdata.run_command(
            f'python -m bang generate --project-dir={project_dir}'
        )

        self.assertTrue(project_dir.has_file("bangfile.py"))
        self.assertTrue(project_dir.has_dir("input"))

