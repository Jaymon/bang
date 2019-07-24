# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

import testdata

from bang.compat import *
from . import TestCase


class PluginTest(TestCase):
    def test_feed(self):
        #from bang.plugins import feed
        s = self.get_project({
            '1/one.md': '1. {}'.format(testdata.get_unicode_words()),
            '2/two.md': '2. {}'.format(testdata.get_unicode_words()),
            '3/three.md': '3. {}'.format(testdata.get_unicode_words()),
        })
        s.output()

        p = os.path.join(String(s.output_dir), 'feed.rss')
        self.assertTrue(os.path.isfile(p))

        body = self.get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)

    def test_sitemap(self):
        #from bang.plugins import sitemap
        s = self.get_project({
            '1/one.md': '1. {}'.format(testdata.get_unicode_words()),
            '2/two.md': '2. {}'.format(testdata.get_unicode_words()),
            '3/three.md': '3. {}'.format(testdata.get_unicode_words()),
        })
        s.output()
        p = os.path.join(String(s.output_dir), 'sitemap.xml')
        self.assertTrue(os.path.isfile(p))

        body = self.get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)


