# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

import testdata

from bang.compat import *
from .. import TestCase


class FeedTest(TestCase):
    def test_feed(self):
        #from bang.plugins import feed
        s = self.get_project({
            '1/one.md': '1. {}'.format(testdata.get_unicode_words()),
            '2/two.md': '2. {}'.format(testdata.get_unicode_words()),
            '3/three.md': '3. {}'.format(testdata.get_unicode_words()),
        }, blog=True)
        s.output()

        p = os.path.join(String(s.output_dir), 'feed.rss')
        self.assertTrue(os.path.isfile(p))

        body = self.get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)

    def test_context_lifecycle(self):
        s = self.get_project({
            'p1/blog_post.md': [
                "foo.jpg"
            ],
            'bangfile.py': [
                "from bang import event",
                "from bang.plugins import blog",
                "",
                "@event('configure')",
                "def global_config(event_name, config):",
                "    config.host = 'example.com'",
                "    config.name = 'example site'",
                "",
                "@event('context.html')",
                "def html_config(event_name, config):",
                "    config.scheme = ''",
                "",
                "@event('context.feed')",
                "def feed_config(event_name, config):",
                "    config.scheme = 'https'",
            ]
        })
        s.output()

        r = s.output_dir.file_contents("feed.rss")
        self.assertTrue("<link>https://example.com" in r)

        post_dir = s.output_dir / "p1"
        r = post_dir.file_contents("index.html")
        self.assertTrue('src="//example.com' in r)


class PluginTest(TestCase):
    def test_sitemap(self):
        s = self.get_project({
            '1/index.md': '1. {}'.format(testdata.get_unicode_words()),
            '2/index.md': '2. {}'.format(testdata.get_unicode_words()),
            '3/index.md': '3. {}'.format(testdata.get_unicode_words()),
        })
        s.output()
        p = os.path.join(String(s.output_dir), 'sitemap.xml')
        self.assertTrue(os.path.isfile(p))

        body = self.get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)


