# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

import testdata

from bang.compat import *
from .. import TestCase as BaseTestCase


class TestCase(BaseTestCase):
    plugins = "amp"


class AmpTest(TestCase):
    def test_image_1(self):
        p = self.get_page([
            "![this is the file](foo.jpg)",
            "",
            "bar.png",
            ""
        ])
        testdata.create_jpg("foo.jpg", tmpdir=p.input_dir)
        testdata.create_png("bar.png", tmpdir=p.input_dir)

        p.config.project.output()

        #pout.v(p.output_dir.file_contents("index.html"))

        self.assertTrue(p.output_dir.has_dir("amp"))
        self.assertTrue(p.output_dir.has_file("amp", "index.html"))

        amp = p.output_dir.file_text("amp", "index.html")
        self.assertTrue("<amp-img" in amp)
        ms = re.findall("<amp-img[^>]+>", amp)
        for m in ms:
            self.assertTrue("width=" in m)
            self.assertTrue("height=" in m)

        html = p.output_dir.file_text("index.html")
        self.assertFalse("<amp-img" in html)

    def test_image_2(self):
        pr = self.get_project(
            input_files={
                "some-page/page.md": [
                    "bar.png",
                ],
                "some-page/bar.png": "",
            },
            project_files={
                "bangfile.py": [
                    "from bang import event",
                    "from bang.plugins import amp",
                    "",
                    "@event('configure.project')",
                    "def configure_project(event, config):",
                    "    config.host = 'localhost:8000'",
                    "    config.scheme = 'http'",
                    "    config.name = 'example site'",
                    ""
                ],
            }
        )

        pr.config.project.output()

        html = pr.output_dir.file_text("some-page/amp/index.html")
        self.assertTrue('height="' in html)
        self.assertTrue('width="' in html)

    def test_canonical(self):
        p = self.get_page()

        p.config.project.output()

        r_html = p.output_dir.file_text("index.html")
        self.assertTrue('rel="amphtml"' in r_html)

        r_amp = p.output_dir.file_text("amp", "index.html")
        self.assertTrue('rel="canonical"' in r_amp)

    def test_css(self):
        p = self.get_page()
        p.config.project.output()
        html = p.output_dir.file_text("amp/index.html")
        self.assertTrue("<style amp-custom>" in html)
        self.assertTrue("<style amp-boilerplate>" in html)

    def test_image_lazyload(self):
        p = self.get_page({
            "page.md": [
                '![this is the file](che.jpg)',
                "",
                "che.jpg",
            ],
            'che.jpg': testdata.create_jpg
        })

        p.output()
        html = p.output_dir.file_text("amp/index.html")
        self.assertEqual(0, html.count('loading="lazy"'))


class AmpEmbedTest(TestCase):
    def setUp(self):
        """This makes sure these tests only run when they are run specifically, so
        these will be skipped when all tests are run, we do this because these tests
        can ping external networks"""
        try:
            import pyt

        except ImportError:
            pass

        else:
            pyt.skip_multi_class("These tests only run when specifically invoked")

        super(AmpEmbedTest, self).setUp()

    def test_embed_youtube(self):
        p = self.get_page([
            "before",
            "",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "",
            "after",
        ])

        p.config.project.output()
        r = p.output_dir.file_text("amp", "index.html")
        self.assertTrue('custom-element="amp-youtube"' in r)
        self.assertTrue('<amp-youtube' in r)

    def test_embed_twitter(self):
        p = self.get_page([
            "before",
            "",
            "https://twitter.com/JohnKirk/status/801086441325375491",
            "",
            "after",
        ])

        p.config.project.output()
        r = p.output_dir.file_text("amp", "index.html")
        self.assertTrue('custom-element="amp-twitter"' in r)
        self.assertTrue('<amp-twitter' in r)

    def test_embed_instagram(self):
        self.skip_test("See the embed plugin instagram test for why this is disabled")
        p = self.get_page([
            "before text",
            "",
            "https://www.instagram.com/p/BNEweVYFVxq/",
            "",
            "after text",
        ])

        p.config.project.output()
        r = p.output_dir.file_text("amp", "index.html")
        self.assertTrue('custom-element="amp-instagram"' in r)
        self.assertTrue('<amp-instagram' in r)

    def test_embed_vimeo(self):
        p = self.get_page([
            "before text",
            "",
            "https://vimeo.com/182739998",
            "",
            "after text",
        ])

        p.config.project.output()
        r = p.output_dir.file_text("amp", "index.html")
        self.assertTrue('custom-element="amp-vimeo"' in r)
        self.assertTrue('<amp-vimeo' in r)

