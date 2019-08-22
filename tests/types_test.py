# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

import testdata

from bang.compat import *
from bang.types import Page, Pages
from . import TestCase


class OtherTest(TestCase):
    def test_md_copy(self):
        p = self.get_project({
            "foo/index.md": "# Foo",
        })

        p.output()
        self.assertFalse(p.output_dir.has_file("foo", "index.md"))


class PageTest(TestCase):
    def test_compile(self):
        p = self.get_page([
            "# this is the title",
            "",
            "body text",
        ])

        p.compile()
        self.assertEqual("this is the title", p.title)
        self.assertTrue(">body text</" in p.html)

    def test_template_name(self):

        class Foo(Page): pass
        class Bar(Foo): pass


        p = self.get_page()
        #c = self.create_config()

        p2 = Bar(p.input_dir, p.output_dir, p.config)

        with self.assertLogs(level="DEBUG") as c:
            p2.output()

        r = "\n".join(c[1])
        for k in ["default.bar", "default.foo", "default.page"]:
            self.assertTrue(k in r)

    def test_page(self):
        p = self.get_page([
                "# title text",
                "",
                "body text",
        ])

        r = p.html
        self.assertRegex(r, r"<h1[^>]*>title text</h1>")
        self.assertRegex(r, r"<p[^>]*>body text</p>")

    def test_description(self):
        p = self.get_page([
            'This is the sentence. This is the second one!!!! And the third. And the fourth.',
            ""
        ])

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one!!!!", desc)

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one!!!!", desc)

        p = self.get_page([
            "This is the sentence.",
            "",
            "This is the second one?!?!?!",
            "And the third. And the fourth.",
            ""
        ])

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one?!?!?!", desc)

        p = self.get_page([
            "This is the first line",
            "",
            "There are no sentences",
            ""
        ])

        desc = p.description
        self.assertEqual("This is the first line There are no sentences", desc)

    def test_absolute_url(self):
        p = self.get_page({
            'index.md': [
                '![this is the file](images/che.jpg)',
                ""
            ]
        })
        self.assertEqual(p.absolute_url("/images/che.jpg"), p.absolute_url("images/che.jpg"))

        p = self.get_page('![this is the file](images/che.jpg)')
        self.assertNotEqual(p.absolute_url("/images/che.jpg"), p.absolute_url("images/che.jpg"))

    def test_other_files(self):
        p = self.get_page({
            "index.md": ["![this is the file](foo.jpg)",
                "",
                "bar.png",
                ""
            ],
            "foo.jpg": "",
            "bar.png": "",
        })

        for of in p.other_files:
            self.assertFalse(of.endswith("index.md"))


class PagesTest(TestCase):
    def test_chunk(self):
        pages = self.get_count_pages(29)

        r = []
        for ps in pages.chunk(10):
            r.append(ps)

        for i, total in enumerate([10, 10, 9]):
            self.assertEqual(total, len(r[i]))

        r = []
        for ps in pages.chunk(10, reverse=True):
            r.append(ps)

        for i, total in enumerate([10, 10, 9]):
            self.assertEqual(total, len(r[i]))

    def test_paginated_output(self):
        pages = self.get_count_pages(21)

        pages.output()
        self.assertTrue(pages.config.output_dir.has_file("index.html"))
        self.assertTrue(pages.config.output_dir.child("page", "2").has_file("index.html"))
        self.assertTrue(pages.config.output_dir.child("page", "3").has_file("index.html"))
        self.assertFalse(pages.config.output_dir.child("page", "4").has_file("index.html"))


