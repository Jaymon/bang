# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from bang.utils import Url
from . import TestCase


class UrlTest(TestCase):
    def test_parts(self):
        u = Url("http://example.com/foo/bar.jpg")

        self.assertTrue(u.is_host("example.com"))
        self.assertTrue(u.is_host("EXAMPLE.COM"))

        self.assertEqual("/foo/bar.jpg", u.path)


