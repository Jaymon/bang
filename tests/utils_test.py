# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from bang.utils import Url, Profile, HTML
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

