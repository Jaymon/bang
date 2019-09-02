# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from bang.utils import Url, Profile, HTML, HTMLStripper
from . import TestCase


class UrlTest(TestCase):
    def test_parts(self):
        u = Url("http://example.com/foo/bar.jpg")

        self.assertTrue(u.is_host("example.com"))
        self.assertTrue(u.is_host("EXAMPLE.COM"))

        self.assertEqual("/foo/bar.jpg", u.path)

    def test_is_local(self):
        u = Url("http://localhost:8000/some-page/bar.png")
        config = self.get_config(host="localhost:8000", scheme="http")
        self.assertTrue(u.is_local(config))

class ProfileTest(TestCase):
    def test_with(self):
        with Profile() as total:
            pass
        self.assertTrue(isinstance(total, Profile))


class HTMLTest(TestCase):
    def test_inject_head(self):
        html = HTML("<html><head></head><body></body></html>")
        r = html.inject_into_head("foo")
        self.assertEqual("<html><head>foo</head><body></body></html>", r)


class HTMLStripperTest(TestCase):
    def test_remove_tags(self):
        hs = HTMLStripper(
            '<div class="foo">1<div>2</div>3</div><div>4</div><p>5</p>',
            remove_tags=["div"]
        )

        plain = hs.get_data()
        self.assertEqual("5", plain)
        return

        hs = HTMLStripper(
            '<div class="foo">1<div>2</div>3</div><div>4</div>',
            remove_tags=["div.foo"]
        )

        plain = hs.get_data()
        self.assertEqual("4", plain)

