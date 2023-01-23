# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

import testdata

from bang.compat import *
from bang.types import Other, Page, Pages
from . import TestCase


class OtherTest(TestCase):
    def test_crud(self):
        relpath = "foo/bar.txt"
        o = self.get_type(Other, relpath)

        output_relpath = o.output_file.relative_to(o.config.output_dir)
        self.assertEqual(relpath, output_relpath)
        self.assertTrue(o.input_file.isfile())
        self.assertFalse(o.output_file.isfile())

        o.output()

        self.assertTrue(o.output_file.isfile())

    def test_file_copy(self):
        p = self.get_project({
            "random.txt": "some random text",
        })

        p.output()

        self.assertTrue(p.input_dir.has_file("random.txt"))
        self.assertTrue(p.output_dir.has_file("random.txt"))


class PageTest(TestCase):
    def test_match(self):
        self.assertTrue(Page.match("page.md"))
        self.assertFalse(Page.match("other.md"))
        self.assertFalse(Page.match("index.md"))

    def test_crud(self):
        p = self.get_page()

        self.assertTrue(p.input_file.isfile())
        self.assertFalse(p.output_file.isfile())

        p.output()

        self.assertTrue(p.output_file.isfile())

    def test_title_1(self):
        """https://github.com/Jaymon/bang/issues/48"""
        pr = self.get_project({
            "page.md": "body text",
        })
        pr.output()

        p = pr.get_types("page")[0]
        self.assertEqual("", p.title)
        html = pr.output_dir.file_text("index.html")
        self.assertFalse("<h1" in html)

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

        class TemplateNameFoo(Page): pass
        class TemplateNameBar(TemplateNameFoo): pass

        with self.assertLogs(level="DEBUG") as c:
            p = self.get_page()
            p2 = TemplateNameBar(p.input_file, p.output_dir, p.config)
            p2.output()

        r = "\n".join(c[1])
        for k in ["default.templatenamebar", "default.templatenamefoo", "default.page"]:
            self.assertTrue(k in r)

    def test_page(self):
        p = self.get_page([
                "# title text",
                "",
                "body text",
        ])

        r = p.html
        self.assertEqual("title text", p.title)
        self.assertRegex(r, r"<p[^>]*>body text</p>")

    def test_description_1(self):
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

    def test_description_2(self):
        """https://github.com/Jaymon/bang/issues/32"""
        p = self.get_page([
            "before",
            "",
            'footnote[^1]',
            "",
            "after",
            "",
            "[^1]: http://example.com",
        ])
        self.assertFalse("footnote1" in p.description)
        self.assertEqual("before footnote after", p.description)

        p = self.get_page([
            "before",
            "",
            '![figcaption](images/che.jpg)',
            "",
            "after",
        ])
        self.assertFalse("figcaption" in p.description)

    def test_absolute_url(self):
        p = self.get_page({
            'page.md': [
                '![this is the file](images/che.jpg)',
                ""
            ]
        })
        self.assertEqual(p.absolute_url("/images/che.jpg"), p.absolute_url("images/che.jpg"))

        p = self.get_page('![this is the file](images/che.jpg)')
        self.assertNotEqual(p.absolute_url("/images/che.jpg"), p.absolute_url("images/che.jpg"))
        self.assertTrue(p.uri in p.absolute_url("images/che.jpg"))
        self.assertFalse(p.uri in p.absolute_url("/images/che.jpg"))


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
        self.assertTrue(pages.config.output_dir.child_dir("page", "2").has_file("index.html"))
        self.assertTrue(pages.config.output_dir.child_dir("page", "3").has_file("index.html"))
        self.assertFalse(pages.config.output_dir.child_dir("page", "4").has_file("index.html"))


