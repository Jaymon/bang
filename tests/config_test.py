# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from bang.config import Config
from . import TestCase


class ConfigTest(TestCase):
    def test_cru(self):
        conf = Config()

        conf.bar = 1
        self.assertEqual(1, conf.bar)

        conf.context_name = "foo"
        self.assertEqual("foo", conf.context_name)
        self.assertFalse("context_name" in conf.fields)

        self.assertEqual(None, conf.che)
        conf.set("che", 2)
        self.assertEqual(2, conf.che)

        del conf.context_name
        self.assertEqual("", conf.context_name)

        conf.bar = 3
        self.assertEqual(3, conf.get("bar"))

    def test_context_with(self):
        config = Config()
        with config.context("foo", bar=1) as conf:
            self.assertEqual("foo", conf.context_name)
            self.assertEqual(1, conf.bar)
        self.assertEqual(None, config.bar)
        self.assertEqual("", conf.context_name)

        with config.context("foo2", bar=2) as conf:
            self.assertEqual(2, conf.bar)

        with config.context("foo") as conf:
            self.assertEqual(1, conf.bar)

    def test_base_url(self):
        config = Config()
        with config.context("web", scheme="", host="example.com") as conf:
            self.assertEqual("//example.com", conf.base_url)

        with config.context("feed", scheme="https", host="example.com") as conf:
            self.assertEqual("https://example.com", conf.base_url)

    def test_context_lifecycle(self):
        s = self.get_site({
            'p1/blog_post.md': [
                "foo.jpg"
            ],
            'bangfile.py': [
                "from bang import event",
                "from bang.plugins import feed",
                "",
                "@event('config')",
                "def global_config(event_name, config):",
                "    config.host = 'example.com'",
                "    config.name = 'example site'",
                "    config.scheme = 'https'",
                "",
                "@event('context.web')",
                "def feed_context_handler(event_name, config):",
                "    config.scheme = ''",
                "",
            ]
        })
        s.output()

        r = s.output_dir.file_contents("feed.rss")
        self.assertTrue("<link>https://example.com" in r)

        post_dir = s.output_dir / "p1"
        r = post_dir.file_contents("index.html")
        self.assertTrue('src="//example.com' in r)

