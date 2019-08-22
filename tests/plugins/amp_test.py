# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from .. import TestCase as BaseTestCase


class TestCase(BaseTestCase):
    @classmethod
    def get_project(cls, input_files=None, project_files=None, bangfile=None):
        bangfile = bangfile or []
        bangfile.insert(0, "from bang.plugins import amp")
        return super(TestCase, cls).get_project(
            input_files,
            project_files,
            bangfile=bangfile
        )


class AmpTest(TestCase):

    def test_image(self):
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

        self.assertTrue(p.output_dir.has_directory("amp"))
        self.assertTrue(p.output_dir.has_file("amp", "index.html"))

        amp = p.output_dir.child_directory("amp").file_contents("index.html")
        pout.v(amp)
        self.assertTrue("<amp-img" in amp)

        amp = p.output_dir.file_contents("index.html")
        self.assertFalse("<amp-img" in amp)


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
        r = p.output_dir.child_directory("amp").file_contents("index.html")
        self.assertTrue('custom-element="amp-youtube"' in r)
        self.assertTrue('<amp-youtube' in r)

        return


        with p.config.context("amp"):
            r = p.html
            pout.v(r)

    def test_embed_twitter(self):
        p = self.get_page([
            "before",
            "",
            "https://twitter.com/JohnKirk/status/801086441325375491",
            "",
            "after",
        ])

        p.config.project.output()
        r = p.output_dir.child_directory("amp").file_contents("index.html")
        self.assertTrue('custom-element="amp-twitter"' in r)
        self.assertTrue('<amp-twitter' in r)

    def test_embed_instagram(self):
        p = self.get_page([
            "before text",
            "",
            "https://www.instagram.com/p/BNEweVYFVxq/",
            "",
            "after text",
        ])

        p.config.project.output()
        r = p.output_dir.child_directory("amp").file_contents("index.html")
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
        r = p.output_dir.child_directory("amp").file_contents("index.html")
        self.assertTrue('custom-element="amp-vimeo"' in r)
        self.assertTrue('<amp-vimeo' in r)

