# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import json
import re

import testdata

from bang.generator import Site
from bang.path import Directory
from bang import skeleton
from bang import config
from . import TestCase
from . import get_body, get_dirs, get_posts, get_post


class PluginTest(TestCase):
    def test_feed(self):
        #from bang.plugins import feed
        s = self.get_site({
            '1/one.md': '1. {}'.format(testdata.get_unicode_words()),
            '2/two.md': '2. {}'.format(testdata.get_unicode_words()),
            '3/three.md': '3. {}'.format(testdata.get_unicode_words()),
            'bangfile.py': [
                "from bang import event",
                "@event('config')",
                "def global_config(event_name, config):",
                "    config.host = 'example.com'",
                "    config.name = 'example site'",
            ]
        })
        s.output()

        p = os.path.join(str(s.output_dir), 'feed.rss')
        self.assertTrue(os.path.isfile(p))

        body = get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)

    def test_sitemap(self):
        #from bang.plugins import sitemap
        s = self.get_site({
            '1/one.md': '1. {}'.format(testdata.get_unicode_words()),
            '2/two.md': '2. {}'.format(testdata.get_unicode_words()),
            '3/three.md': '3. {}'.format(testdata.get_unicode_words()),
            'bangfile.py': [
                "from bang import event",
                "@event('config')",
                "def global_config(event_name, config):",
                "    config.host = 'example.com'",
            ]
        })
        s.output()
        p = os.path.join(str(s.output_dir), 'sitemap.xml')
        self.assertTrue(os.path.isfile(p))

        body = get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)


class SiteTest(TestCase):
    def test_single_document(self):
        s = self.get_site({
            './index.md': 'aux text',
            './aux.jpg': '',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("index.html"))
        self.assertTrue(s.output_dir.has_file("aux.jpg"))

    def test_file_structure(self):
        s = self.get_site({
            './one.jpg': '',
            './two.txt': 'some text',
            'other/three.txt': 'third text',
            'post/foo.md': 'post text',
            'aux/index.md': 'aux text',
        })
        s.output()

        self.assertTrue(s.output_dir.has_file("one.jpg"))
        self.assertTrue(s.output_dir.has_file("two.txt"))
        self.assertTrue(s.output_dir.child("other").has_file("three.txt"))
        self.assertTrue(s.output_dir.child("post").has_file("index.html"))
        self.assertTrue(s.output_dir.child("aux").has_file("index.html"))

    def test_unicode_output(self):
        project_dir, output_dir = get_dirs({
            'input/aux/index.md': testdata.get_unicode_words(),
        })

        s = Site(project_dir, output_dir)
        s.output()

        self.assertTrue(os.path.isfile(os.path.join(str(output_dir), 'aux', 'index.html')))

    def test_drafts(self):
        project_dir, output_dir = get_dirs({
            'input/_draft/foo.md': testdata.get_words(),
            'input/notdraft/_bar.md': testdata.get_words(),
        })

        s = Site(project_dir, output_dir)
        s.output()

        self.assertFalse(os.path.isfile(os.path.join(str(output_dir), '_draft', 'index.html')))
        self.assertFalse(os.path.isfile(os.path.join(str(output_dir), 'notdraft', 'index.html')))
        self.assertEqual(0, len(s.posts))

    def test_regex_compile(self):
        project_dir, output_dir = get_dirs({
            'input/foo/post1.md': testdata.get_unicode_words(),
            'input/foo2/post2.md': testdata.get_unicode_words(),
            'input/bar/post3.md': testdata.get_unicode_words(),
            'input/bar/fake.jpg': "",
        })

        s = Site(project_dir, output_dir)

        s.output(r"bar")
        count = 0
        for p in s.posts:
            if p.output_dir.exists():
                count += 1
        self.assertEqual(1, count)

        s.output(r"bar")
        count = 0
        for p in s.posts:
            if p.output_dir.exists():
                count += 1
        self.assertEqual(1, count)

        s.output()
        count = 0
        for p in s.posts:
            if p.output_dir.exists():
                count += 1
        self.assertEqual(3, count)

    def test_private_post(self):
        project_dir, output_dir = get_dirs({
            'input/_foo/post1.md': testdata.get_unicode_words(),
            'input/_foo/fake.jpg': "",
            'input/_bar/other/something.jpg': "",
        })

        s = Site(project_dir, output_dir)

        s.output()
        self.assertIsNone(s.posts.first_post)
        self.assertEqual(1, len(s.others))


class SkeletonTest(TestCase):
    def test_generate(self):
        project_dir = Directory(testdata.create_dir())
        s = skeleton.Skeleton(project_dir)
        s.output()

        for file_dict in skeleton.file_skeleton:
            d = project_dir / file_dict['dir']
            self.assertTrue(d.exists())
            self.assertTrue(os.path.isfile(os.path.join(str(d), file_dict['basename'])))


class EmbedPluginTest(TestCase):

    def setUp(self):
        """This makes sure these tests only run when they are run specifically, so
        these will be skipped when all tests are run, we do this because these tests
        can ping external networks"""
        if 'PYT_TEST_CLASS_COUNT' in os.environ:
            skip = True
            pyt_cls_count = int(os.environ['PYT_TEST_CLASS_COUNT'])
            pyt_test_count = int(os.environ['PYT_TEST_COUNT'])
            pyt_mod_count = int(os.environ['PYT_TEST_MODULE_COUNT'])
            #pout.v(pyt_cls_count, pyt_test_count, pyt_mod_count)

            if pyt_cls_count == 1:
                skip = False

            elif pyt_test_count == 1:
                skip = False

            elif pyt_mod_count == 1:
                skip = False

            if skip:
                raise self.skipTest("takes too long")

        super(EmbedPluginTest, self).setUp()


    def test_embed_link(self):
        p = get_post({
            'linkify.md': "\n".join([
                "This is some [text](http://bar.com) < and then there > is just a url",
                "",
                "http://foo.com",
                "",
                "another [link **with** tags](http://che.com) text after",
            ])
        })

        r = p.html
        self.assertTrue('<a class="embed" href="http://foo.com">http://foo.com</a>' in r)
        self.assertEqual(1, r.count("embed"))

    def test_embed_youtube(self):
        p = get_post({
            'embed_youtube.md': "\n".join([
                "before",
                "",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "",
                "after",
            ])
        })

        r = p.html
        self.assertTrue("<figure" in r)

    def test_embed_youtube_2(self):
        p = get_post({
            'embed_yt2.md': """12 notes, that's all you get! These 12 notes give us everything from [Beethoven's 5th symphony](https://www.youtube.com/watch?v=_4IRMYuE1hI) to [Hanson's MMMBop](https://www.youtube.com/watch?v=NHozn0YXAeE), and everything in between. They all use the same set of 12 notes"""
        })

        r = p.html
        self.assertFalse("<iframe" in r)

    def test_embed_twitter(self):
        p = get_post({
            'embed_twitter.md': "\n".join([
                "before",
                "",
                "https://twitter.com/JohnKirk/status/801086441325375491",
                "",
                "middle",
                "",
                "https://twitter.com/foo/status/100",
                "",
                "after",
            ]),
            "twitter.json": json.dumps({
                "https://twitter.com/foo/status/100": {
                    'html': "".join([
                        '<blockquote class="twitter-tweet">',
                        '<p lang="en" dir="ltr">foo</p>',
                        '&mdash; foo <a href="https://twitter.com/foo/status/100">month DD, YYYY</a>',
                        '</blockquote>',
                    ]),
                },
            }),
        })

        r = p.html
        self.assertEqual(2, r.count("<figure"))

        contents = json.loads(p.input_dir.file_contents("twitter.json"))
        self.assertEqual(2, len(contents))

    def test_no_embed_twitter_links(self):
        p = get_post({
            'no_embed_twitter.md': "\n".join([
                "[@Jaymon](https://twitter.com/jaymon)",
            ]),
        })

        r = p.html
        self.assertTrue("a href" in r)

    def test_embed_instagram(self):
        p = get_post({
            'embed_instagram.md': "\n".join([
                "before text",
                "",
                "https://www.instagram.com/p/BNEweVYFVxq/",
                "",
                "after text",
            ]),
        })

        r = p.html
        self.assertEqual(1, r.count("<figure"))

        contents = json.loads(p.input_dir.file_contents("instagram.json"))
        self.assertEqual(1, len(contents))
        self.assertTrue(p.input_dir.has_file("BNEweVYFVxq.jpg"))

    def test_embed_vimeo(self):
        p = get_post({
            'embed_vimeo.md': "\n".join([
                "before text",
                "",
                "https://vimeo.com/182739998",
                "",
                "after text",
            ]),
        })

        r = p.html
        self.assertEqual(1, r.count("<figure"))

    def test_embed_image(self):
        p = get_post({
            'bogus.jpg': "",
            'embed_image.md': "\n".join([
                "before text",
                "",
                "bogus.jpg",
                "",
                "after text",
            ]),
        })

        r = p.html
        self.assertTrue('alt="bogus.jpg"' in r)
        self.assertTrue('title=""' in r)

    def test_embed_image_url(self):
        p = get_post({
            'bogus.jpg': "",
            'embed_image.md': "\n".join([
                "before text",
                "",
                "http://embedded.com/full/url/bogus.jpg",
                "",
                "after text",
            ]),
        })

        r = p.html
        self.assertTrue('alt="bogus.jpg"' in r)
        self.assertTrue('title=""' in r)
        self.assertTrue('src="http://embedded.com/full/url/bogus.jpg"' in r)

    def test_embed_highlight(self):
        p = get_post({
            'embed_highlight.md': "\n".join([
                "```",
                "",
                "https://foo.com",
                "",
                "```",
            ])
        })

        r = p.html
        self.assertFalse("embed" in r)


class DirectoryTest(TestCase):
    def test_in_private(self):
        d = Directory(testdata.create_dir("/foo/_bar/che"))
        self.assertTrue(d.in_private())
        self.assertFalse(d.is_private())

        d = Directory(testdata.create_dir("/foo/_bar"))
        self.assertTrue(d.in_private())
        self.assertTrue(d.is_private())

