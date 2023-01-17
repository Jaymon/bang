# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from bang.compat import *
from bang.config import (
    Config,
    Theme,
)
from . import TestCase, testdata


class ThemeTest(TestCase):
    def test_default(self):
        c = self.create_config()
        self.assertEqual("default", c.theme_name)

    def test_custom_theme(self):
        theme_name = "foobar"
        project_files = {
            'bangfile.py': [
                "from bang import event",
                "@event('configure')",
                "def theme_config(event_name, config):",
                "    config.theme_name = '{}'".format(theme_name),
                ""
            ],
            'themes/{}/input/assets/app.css'.format(theme_name): "",
            'themes/{}/input/assets/app.js'.format(theme_name): "",
            'themes/{}/template/page.html'.format(theme_name): "{{ instance.title }}\n{{ instance.html }}\n",
            'themes/{}/template/pages.html'.format(theme_name): "\n".join([
                "{% for instance in instances %}",
                "{% include 'page.html' %}",
                "<hr>",
                "{% endfor %}",
                "",
            ])
        }

        s = self.get_project(project_files=project_files)

        self.assertEqual(theme_name, s.config.theme_name)

        t = s.config.theme
        t.output()

        self.assertTrue(s.config.output_dir.has_file("assets/app.css"))
        self.assertTrue(s.config.output_dir.has_file("assets/app.js"))

    def test_has_template(self):
        theme_dir = testdata.create_files({
            "template/foo.html": "foo",
            "template/che.html": "che",
            "template/bar/baz.html": "baz",
        })

        t = Theme(theme_dir, testdata.mock(get=""))
        self.assertTrue(t.has_template("foo"))
        self.assertTrue(t.has_template("che"))
        self.assertTrue(t.has_template("bar/baz"))


class ConfigTest(TestCase):
    def test_base_url(self):
        config = self.create_config()
        with config.context("web", scheme="", host="example.com") as conf:
            self.assertEqual("//example.com", conf.base_url)

        with config.context("feed", scheme="https", host="example.com") as conf:
            self.assertEqual("https://example.com", conf.base_url)

        with config.context("no_host_no_scheme", scheme="", host="") as conf:
            self.assertEqual("", conf.base_url)

        with config.context("no_host_scheme", scheme="http", host="") as conf:
            self.assertEqual("", conf.base_url)

        with config.context("host_none_scheme", scheme="http", host=None) as conf:
            self.assertEqual("", conf.base_url)

        with config.context("none_host_and_scheme", scheme=None, host=None) as conf:
            self.assertEqual("", conf.base_url)

