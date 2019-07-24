# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from bang.compat import *
from bang.config import Config
from . import TestCase


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
            'themes/{}/template/aux.html'.format(theme_name): "{{ aux.title }}\n{{ aux.html }}\n",
            'themes/{}/template/post.html'.format(theme_name): "{{ post.title }}\n{{ post.html }}\n",
            'themes/{}/template/posts.html'.format(theme_name): "\n".join([
                "{% for post in posts %}",
                "{% include 'post.html' %}",
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


class ConfigTest(TestCase):
    def test_context_with(self):
        config = self.create_config()
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
        config = self.create_config()
        with config.context("web", scheme="", host="example.com") as conf:
            self.assertEqual("//example.com", conf.base_url)

        with config.context("feed", scheme="https", host="example.com") as conf:
            self.assertEqual("https://example.com", conf.base_url)

    def test_context_lifecycle(self):
        s = self.get_project({
            'p1/blog_post.md': [
                "foo.jpg"
            ],
            'bangfile.py': [
                "from bang import event",
                "from bang.plugins import feed",
                "",
                "@event('configure')",
                "def global_config(event_name, config):",
                "    config.host = 'example.com'",
                "    config.name = 'example site'",
                "",
                "@event('context.web')",
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

    def test_context_hierarchy(self):
        """https://github.com/Jaymon/bang/issues/33"""
        config = self.create_config()
        config.foo = False

        with config.context("foo") as c:
            c.foo = True
            self.assertEqual("foo", c.context_name)
            self.assertTrue(c.foo)

            with config.context("bar") as c:
                self.assertEqual("bar", c.context_name)
                self.assertTrue(c.foo)
                c.foo = False

                with config.context("che") as c:
                    # should be in che context here
                    self.assertEqual("che", c.context_name)
                    self.assertFalse(c.foo)

                # should be in bar context here
                self.assertEqual("bar", c.context_name)
                self.assertFalse(c.foo)

            #should be in foo context here
            self.assertEqual("foo", c.context_name)
            self.assertTrue(c.foo)

        # should be in "" context here
        self.assertEqual("", c.context_name)
        self.assertFalse(c.foo)


