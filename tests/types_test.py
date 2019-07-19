# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

import testdata

from bang.compat import *
from bang.types import Post, Aux, Types
from . import TestCase
from . import get_body, get_dirs, get_posts, get_post


class TypesTest(TestCase):
    def test_pages(self):
        s = self.get_project({})
        posts = Types(s)
        for x in range(29):
            p = Post(s.input_dir, s.output_dir, s)
            #p.body = x
            posts.append(p)

        r = []
        for ps in posts.pages(10):
            r.append(ps)

        for i, total in enumerate([10, 10, 9]):
            self.assertEqual(total, len(r[i]))

        r = []
        for ps in posts.pages(10, reverse=True):
            r.append(ps)

        for i, total in enumerate([10, 10, 9]):
            self.assertEqual(total, len(r[i]))

    def test_paginated_output(self):
        posts = self.get_count_posts(21)

        posts.output()
        self.assertTrue(posts.config.output_dir.has_file("index.html"))
        self.assertTrue(posts.config.output_dir.child("page", "2").has_file("index.html"))
        self.assertTrue(posts.config.output_dir.child("page", "3").has_file("index.html"))
        self.assertFalse(posts.config.output_dir.child("page", "4").has_file("index.html"))


class PostTest(TestCase):
    def test_no_bangfile_host(self):
        name = testdata.get_ascii(16)
        ps = self.get_posts({
            '{}/foo.md'.format(name): "\n".join([
                "hi"
            ]),
            'bangfile.py': ""
        })

        self.assertRegexpMatches(ps.first_page.url, "^/{}$".format(name))

    def test_description_property(self):
        p = get_post({
            'foo.md': "\n".join([
                'This is the sentence. This is the second one!!!! And the third. And the fourth.',
                ""
            ])
        })

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one!!!!", desc)

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one!!!!", desc)

        p = get_post({
            'foo.md': "\n".join([
                "This is the sentence.",
                "",
                "This is the second one?!?!?!",
                "And the third. And the fourth.",
                ""
            ])
        })

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one?!?!?!", desc)

        p = get_post({
            'foo.md': "\n".join([
                "This is the first line",
                "",
                "There are no sentences",
                ""
            ])
        })

        desc = p.description
        self.assertEqual("This is the first line There are no sentences", desc)


class AuxTest(TestCase):
    def test_aux(self):
        p = get_post({
            'index.md': "\n".join([
                "# title text",
                "",
                "body text",
            ])
        })

        r = p.html

