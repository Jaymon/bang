# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

import testdata

from bang.compat import *
from bang.path import Directory
from bang.plugins.favicon import Favicons
from bang.plugins import favicon
from .. import TestCase


class FeedTest(TestCase):
    @classmethod
    def get_project(cls, input_files=None, project_files=None, bangfile=None):
        bangfile = bangfile or []
        bangfile.insert(0, "from bang.plugins import blog")
        return super(FeedTest, cls).get_project(
            input_files,
            project_files,
            bangfile=bangfile
        )

    def test_feed(self):
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


class SitemapTest(TestCase):
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


class FaviconTest(TestCase):
    plugins = "favicon"

    @classmethod
    def get_dirs(cls, project_files=None):
        project_dir, output_dir = super(FaviconTest, cls).get_dirs(project_files)

        d = String(project_dir.child_directory("input"))
        testdata.create_ico("favicon.ico", tmpdir=d),
        testdata.create_png("favicon-32.png", tmpdir=d, width=32, height=32),
        testdata.create_png("favicon-192.png", tmpdir=d, width=192, height=192),
        testdata.create_png("favicon-228.png", tmpdir=d, width=228, height=228),
        testdata.create_png("favicon-196.png", tmpdir=d, width=196, height=196),
        testdata.create_png("favicon-180.png", tmpdir=d, width=180, height=180),

        return project_dir, output_dir

#     @classmethod
#     def get_project(cls, input_files=None, project_files=None, bangfile=None):
#         bangfile = bangfile or []
#         bangfile.insert(0, "from bang.plugins import favicon")
#         return super(FaviconTest, cls).get_project(
#             input_files,
#             project_files,
#             bangfile=bangfile
#         )

    def get_favicons(self):
        p = self.get_project()
        f = favicon.Favicons(p.input_dir)
        return f

    def test_get_info(self):
        f = self.get_favicons()
        info = f.get_info()
        self.assertEqual(6, len(info))

    def test_html(self):
        f = self.get_favicons()
        html = f.html()
        self.assertTrue('rel="icon"' in html)
        self.assertTrue('rel="shortcut-icon"' in html)
        self.assertTrue('rel="apple-touch-icon"' in html)

    def test_inject(self):
        p = self.get_page()
        p.output()
        html = p.output_dir.file_contents("index.html")
        self.assertTrue('rel="icon"' in html)
        self.assertTrue('rel="shortcut-icon"' in html)
        self.assertTrue('rel="apple-touch-icon"' in html)


class GoogleAnalyticsTest(TestCase):
    plugins = "googleanalytics"

    def test_html_context(self):
        p = self.get_page()
        p.config.ga_tracking_id = "XX-DDDDDDDD-D"
        p.output()
        html = p.output_dir.file_contents("index.html")
        self.assertTrue("gtag('config', 'XX-DDDDDDDD-D')" in html)

    def test_amp_context(self):
        p = self.get_page(bangfile="from bang.plugins import amp")
        p.config.ga_tracking_id = "XX-DDDDDDDD-D"
        p.config.project.output()

        html = p.output_dir.file_contents("index.html")
        self.assertTrue("gtag('config', 'XX-DDDDDDDD-D')" in html)

        html = p.output_dir.file_contents("amp/index.html")
        self.assertTrue("<amp-analytics " in html)


class OpenGraphTest(TestCase):
    plugins = "opengraph"
    def test_html(self):
        p = self.get_page()
        p.output()
        html = p.output_dir.file_contents("index.html")
        for s in ["og:url", "og:type", "og:title", "og:description", "og:image"]:
            self.assertTrue(s in html)


class BreadcrumbsTest(TestCase):
    plugins = "breadcrumbs"

    def test_breadcrumbs(self):
        p = self.get_project({
            "foo/bar/index.md": "",
            "foo/che/index.md": "",
            "foo/boo/index.md": "",
            "baz/bam/index.md": "",
        })
        p.output()

        html = p.output_dir.file_contents("foo/index.html")
        self.assertTrue(">/foo/bar" in html)
        self.assertTrue(">/foo/boo" in html)
        self.assertTrue(">/foo/che" in html)

