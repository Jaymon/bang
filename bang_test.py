from unittest import TestCase
import os
import codecs
import sys
import json
import re

import testdata

from bang.generator import Post, Site, Template
from bang.path import Directory, ProjectDirectory
from bang import skeleton
from bang import config
from bang.__main__ import configure_logging


# configure root logger
# import logging
# import sys
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# log_handler = logging.StreamHandler(stream=sys.stderr)
# log_formatter = logging.Formatter('[%(levelname)s] %(message)s')
# log_handler.setFormatter(log_formatter)
# logger.addHandler(log_handler)


# "" to turn on all logging for the tests
configure_logging("DI")


def get_body(filepath):
    v = u''
    with codecs.open(filepath, 'r+', 'utf-8') as fp:
        v = fp.read()
    return v


def get_dirs(input_files):

    # TODO -- switch these to use the skeleton templates
    d = {
        'template/aux.html': "{{ aux.title }}\n{{ aux.html }}\n",
        'template/post.html': "{{ post.title }}\n{{ post.html }}\n{{ post.modified.strftime('%Y-%m-%d') }}\n",
        'template/posts.html': "\n".join([
            "{% for post in posts.reverse(10) %}",
            "{% include 'post.html' %}",
            "<hr>",
            "{% endfor %}",
            "",
        ])
    }
    d.update(input_files)

    output_dir = Directory(testdata.create_dir())
    project_dir = ProjectDirectory(testdata.create_dir())

    testdata.create_files(d, tmpdir=str(project_dir))
    return project_dir, output_dir


def get_posts(post_files):

    # clear the environment
    for k, v in os.environ.items():
        if k.startswith('BANG_'):
            del os.environ[k]
    sys.modules.pop("bangfile_module", None)

    di = {
        'bangfile.py': [
            "host = 'example.com'",
            "name = 'example site'",
            ""
        ]
    }

    # replace any project files if they are present
    for rp in di.keys():
        if rp in post_files:
            di[rp] = post_files.pop(rp)

    for basename, file_contents in post_files.items():
        name = testdata.get_ascii(16)
        fp = os.path.join('input', name, basename)
        di[fp] = file_contents

    project_dir, output_dir = get_dirs(di)

#     d = Directory(project_dir.input_dir, name)
#     d.ancestor_dir = project_dir.input_dir
#     tmpl = Template(project_dir.template_dir)
#     p = Post(d, output_dir, tmpl, Config(project_dir))

    s = Site(project_dir, output_dir)
    s.output()

    #pout.v(s, len(s.posts), len(s.auxs))

    return s.posts if len(s.posts) else s.auxs

def get_post(*args, **kwargs):
    posts = get_posts(*args, **kwargs)
    return posts.first_post
    #return s.posts.first_post if len(s.posts) else s.auxs.first_post


class PluginTest(TestCase):
    def test_feed(self):
        from bang.plugins import feed
        project_dir, output_dir = get_dirs({
            'input/1/one.md': u'1. {}'.format(testdata.get_unicode_words()),
            'input/2/two.md': u'2. {}'.format(testdata.get_unicode_words()),
            'input/3/three.md': u'3. {}'.format(testdata.get_unicode_words()),
            'bangfile.py': "\n".join([
                "host = 'example.com'",
                "name = 'example site'",
                ""
            ])
        })
        s = Site(project_dir, output_dir)
        s.output()

        p = os.path.join(str(s.output_dir), 'feed.rss')
        self.assertTrue(os.path.isfile(p))

        body = get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)

    def test_sitemap(self):
        from bang.plugins import sitemap
        project_dir, output_dir = get_dirs({
            'input/1/one.md': u'1. {}'.format(testdata.get_unicode_words()),
            'input/2/two.md': u'2. {}'.format(testdata.get_unicode_words()),
            'input/3/three.md': u'3. {}'.format(testdata.get_unicode_words()),
            'bangfile.py': "\n".join([
                "host = 'example.com'",
                ""
            ])
        })
        s = Site(project_dir, output_dir)

        s.output()
        p = os.path.join(str(s.output_dir), 'sitemap.xml')
        self.assertTrue(os.path.isfile(p))

        body = get_body(p)
        self.assertTrue('example.com/1' in body)
        self.assertTrue('example.com/2' in body)
        self.assertTrue('example.com/3' in body)


class SiteTest(TestCase):
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
        self.assertIsNone(s.others.first_post)


class PostTest(TestCase):
    def test_no_bangfile_host(self):
        name = testdata.get_ascii(16)
        p = get_post({
            '{}/foo.md'.format(name): "\n".join([
                "hi"
            ]),
            'bangfile.py': ""
        })

        #self.assertEqual("/{}".format(name), p.url)
        self.assertRegexpMatches(p.url, "^/[^/]+/{}$".format(name))

    def test_description_property(self):
        p = get_post({
            'foo.md': "\n".join([
                'This is the sentence. This is the second one!!!! And the third. And the fourth.',
                ""
            ])
        })

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one!!!!", desc)

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one!!!!", desc)

        p = get_post({
            'foo.md': "\n".join([
                "This is the sentence.",
                "",
                "This is the second one?!?!?!",
                "And the third. And the fourth.",
                ""
            ])
        })

        desc = p.description
        self.assertEqual("This is the sentence. This is the second one?!?!?!", desc)

        p = get_post({
            'foo.md': "\n".join([
                "This is the first line",
                "",
                "There are no sentences",
                ""
            ])
        })

        desc = p.description
        self.assertEqual("This is the first line There are no sentences", desc)

    def test_image_property(self):
        p = get_post({
            'images/che.jpg': "",
            'foo.md': "\n".join([
                '![this is the file](images/che.jpg)',
                ""
            ])
        })

        im = p.image
        self.assertTrue(im.endswith("images/che.jpg"))

        im = p.image
        self.assertTrue(im.endswith("images/che.jpg"))

    def test_image_full_path(self):
        p = get_post({
            'images/che.jpg': "",
            'foo.md': "\n".join([
                '![this is the file](images/che.jpg)',
                ""
            ])
        })
        self.assertRegexpMatches(p.html, '//{}/[^/]+/images/che.jpg'.format(p.config.host))


    def test_image_figure(self):
        p = get_post({
            'figure.md': "\n".join([
                "this is some text before the image",
                "",
                "![this is the caption](foo.jpg)",
                "",
                "this is some text after the image",
                "",
                "This text has an image ![](bar.jpg)",
                "",
                "![](che.jpg) this text after an image",
                "",
                "![](baz.jpg) this text after an image with [link](http://baz.com)",
            ])
        })
        r = p.html
        self.assertTrue('<figure><img alt="foo.jpg" src=' in r)
        self.assertTrue('<p>This text has an image <img alt="bar.jpg" src=' in r)
        self.assertTrue('<p><img alt="che.jpg" src=' in r)
        self.assertTrue('<p><img alt="baz.jpg" src=' in r)

    def test_image_position(self):
        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '[![this is the alt](che.jpg "this is the title")](http://example.com)',
                ""
            ])
        })
        r = p.html
        self.assertTrue("figure" in r)
        self.assertTrue("example.com" in r)
        self.assertTrue("figcaption" in r)
        self.assertTrue("img" in r)

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![this is the file](che.jpg)',
                ""
            ])
        })
        r = p.html
        self.assertTrue("figure" in r)
        self.assertTrue("figcaption" in r)

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![this is the file](che.jpg) and some text',
                ""
            ])
        })
        r = p.html
        self.assertFalse("figure" in r)
        self.assertFalse("figcaption" in r)
        self.assertTrue("img" in r)
        self.assertTrue("title=" in r)

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                'and this has some text in front of the image ![this is the file](che.jpg)',
                ""
            ])
        })
        r = p.html
        self.assertFalse("figure" in r)
        self.assertFalse("figcaption" in r)
        self.assertTrue("img" in r)
        self.assertTrue("title=" in r)

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                'all business in the front ![this is the file](che.jpg) and a party in the back',
                ""
            ])
        })
        r = p.html
        self.assertFalse("figure" in r)
        self.assertFalse("figcaption" in r)
        self.assertTrue("img" in r)
        self.assertTrue("title=" in r)

    def test_image_title_alt(self):
        # alt = "alternate", title = ""
        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![alternate](che.jpg "")',
                ""
            ])
        })
        r = p.html
        self.assertTrue('title=""' in r)
        self.assertTrue('alt="alternate"' in r)

        # alt = "alternate", title = "image title"
        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![alternate](che.jpg "image title")',
                ""
            ])
        })
        r = p.html
        self.assertTrue('title="image title"' in r)
        self.assertTrue('alt="alternate"' in r)

        # alt = "alternate", title = None
        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![alternate](che.jpg)',
                ""
            ])
        })
        r = p.html
        self.assertTrue('title="alternate"' in r)
        self.assertTrue('alt="che.jpg"' in r)

        # alt = "", title = "image title"
        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![](che.jpg "image title")',
                ""
            ])
        })
        r = p.html
        self.assertTrue('title="image title"' in r)
        self.assertTrue('alt="che.jpg"' in r)

    def test_attr(self):
        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![this is the file](che.jpg){: .centered }',
                ""
            ])
        })

        self.assertRegexpMatches(p.html, 'class=\"centered')

    def test_href(self):
        p = get_post({
            'che.txt': testdata.get_words(),
            'foo.md': "\n".join([
                "full [link](http://foo.com)",
                "full [path](/bar)",
                "file [path](che.txt)",
                "file [relative link](//bar.com)",
                ""
            ])
        })

        html = p.html
        self.assertRegexpMatches(html, '\"http://foo.com\"')
        self.assertRegexpMatches(html, '\"//{}/bar\"'.format(p.config.host))
        self.assertRegexpMatches(html, '\"//{}/[^\/]+/che.txt\"'.format(p.config.host))
        self.assertRegexpMatches(html, '\"//bar.com\"')

    def test_codeblocks(self):
        p = get_post({
            'blocks.md': "\n".join([
                "```python",
                #"```no-highlight",
                "s = 'here we are'",
                "```"
            ])
        })

        self.assertRegexpMatches(p.html, '<code class=\"codeblock python\">')

    def test_codeblocks_2(self):
        content = u"\n".join([
            u'this is the post',
            u'',
            u'```python',
            u'def foo():',
            u'    pass',
            u'```',
            ''
        ])
        p = get_post({'this is the post.md': content})
        r = p.html
        self.assertRegexpMatches(r, 'class=\"codeblock python\"')

    def test_easy_links(self):
        p = get_post({
            'easy_links_1.md': "\n".join([
                "[first][n]",
                "[n]: http://first.com",
                "",
                "[second][n]",
                "[n]: http://second.com",
                "",
                "[third][foo]",
                "[foo]: http://third.com",
            ])
        })

        r = p.html
        for x in ["first", "second", "third"]:
            self.assertTrue(x in r)
            self.assertTrue("{}.com".format(x) in r)

    def test_easy_footnotes(self):
        p = get_post({
            'easy_footnotes_1.md': "\n".join([
                "first text[^n]",
                "[^n]: first footnote",
                "",
                "second text[^n]",
                "[^n]: second footnote",
                "",
                "third text[^foo]",
                "[^foo]: third footnote",
            ])
        })

        r = p.html
        for x in ["1", "2", "foo"]:
            #self.assertTrue("#fn-2-{}".format(x) in r)
            #self.assertTrue("#fnref-2-{}".format(x) in r)
            self.assertRegexpMatches(r, "#fn-\d+-{}".format(x))
            self.assertRegexpMatches(r, "#fnref-\d+-{}".format(x))

    def test_uniq_footnotes(self):
        ps = get_posts({
            'uniq_footnotes_1.md': [
                "first text[^n]",
                "[^n]: first footnote",
            ],
            'uniq_footnotes_2.md': [
                "second text[^n]",
                "[^n]: second footnote",
            ],
            'uniq_footnotes_3.md': [
                "third text[^n]",
                "[^n]: third footnote",
            ]
        })

        uniqs = set()
        for i, p in enumerate(ps):
            r = p.html
            m = re.search(r"#fn-(\d+)-\d+", r)
            uniqs.add(m.group(1))

            m = re.search(r"#fnref-(\d+)-\d+", r)
            uniqs.add(m.group(1))

        self.assertEqual(3, len(uniqs))

    def test_easy_images(self):
        p = get_post({
            'easy_images_1.md': "\n".join([
                "![foo title](foo.jpg)"
            ])
        })
        r = p.html
        self.assertTrue('alt="foo.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = get_post({
            'easy_images_1.md': "\n".join([
                "![fooalt.jpg](foo.jpg \"foo title\")"
            ])
        })
        r = p.html
        self.assertTrue('alt="fooalt.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = get_post({
            'easy_images_1.md': "\n".join([
                "![foo title][n]",
                "[n]: foo.jpg",
            ])
        })
        r = p.html
        self.assertTrue('alt="foo.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = get_post({
            'easy_images_1.md': "\n".join([
                "![fooalt.jpg][n]",
                "[n]: foo.jpg \"foo title\"",
            ])
        })
        r = p.html
        self.assertTrue('alt="fooalt.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = get_post({
            'easy_images_1.md': "\n".join([
                "![](foo.jpg)",
            ])
        })
        r = p.html
        self.assertTrue('alt="foo.jpg"' in r)
        self.assertFalse('title' in r)

    def test_meta(self):
        p = get_post({
            'meta.md': "\n".join([
                "foo: bar",
                "tags: one, two, three",
                "",
                "This is the first sentence"
            ])
        })

        r = p.html
        self.assertEqual("<p>This is the first sentence</p>", p.html)
        self.assertTrue("foo" in p.meta)

    def test_html_entities_codeblock(self):
        p = get_post({
            'embed_highlight.md': "\n".join([
                "```",
                "<b>This is html in a code block</b>",
                "```",
            ])
        })

        r = p.html
        self.assertEqual(2, r.count("&lt;"))
        self.assertEqual(2, r.count("&gt;"))

    def test_admonition(self):

        body = []
        admonitions = [
            #"attention",
            #"caution",
            #"danger",
            #"error",
            #"hint",
            #"important",
            #"note",
            #"tip",
            #"warning",
            "error",
            "notice",
            "info",
            "success",
        ]

        for a in admonitions:
            body.extend([
                "!!! {}".format(a),
                "    this is an {} admonition".format(a)
            ])


        p = get_post({
            "admonition.md": body
        })

        r = p.html
        self.assertEqual(4, r.count("admonition-title"))


class AuxTest(TestCase):
    def test_aux(self):
        p = get_post({
            'index.md': "\n".join([
                "# title text",
                "",
                "body text",
            ])
        })

        r = p.html


class SkeletonTest(TestCase):
    def test_generate(self):
        project_dir = ProjectDirectory(testdata.create_dir())
        s = skeleton.Skeleton(project_dir)
        s.output()

        for file_dict in skeleton.file_skeleton:
            d = project_dir / file_dict['dir']
            self.assertTrue(d.exists())
            self.assertTrue(os.path.isfile(os.path.join(str(d), file_dict['basename'])))


class EmbedPluginTest(TestCase):
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

        contents = json.loads(p.directory.file_contents("twitter.json"))
        self.assertEqual(2, len(contents))

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

        contents = json.loads(p.directory.file_contents("instagram.json"))
        self.assertEqual(1, len(contents))
        self.assertTrue(p.directory.has_file("BNEweVYFVxq.jpg"))

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


class ConfigTest(TestCase):
    def test_context(self):
        with config.context("foo", bar=1) as conf:
            self.assertEqual(1, conf.bar)

        with config.context("foo2", bar=2) as conf:
            self.assertEqual(2, conf.bar)

        with config.context("foo") as conf:
            self.assertEqual(1, conf.bar)

    def test_base_url(self):
        with config.context("web", scheme="", host="example.com") as conf:
            self.assertEqual("//example.com", conf.base_url)

        with config.context("feed", scheme="https", host="example.com") as conf:
            self.assertEqual("https://example.com", conf.base_url)

    def test_context_lifecycle(self):
        project_dir, output_dir = get_dirs({
            'input/p1/blog_post.md': [
                "foo.jpg"
            ],
            "input/bogus.jpg": "",
            'bangfile.py': [
                "from bang import event",
                "from bang.plugins import feed",
                "host = 'example.com'",
                "name = 'example site'",
                "",
                "scheme = 'https'",
                "@event.bind('context.web')",
                "def feed_context_handler(event_name, config):",
                "    config.scheme = ''",
                "",
            ]
        })

        s = Site(project_dir, output_dir)
        s.output()

        r = output_dir.file_contents("feed.rss")
        self.assertTrue("<link>https://example.com" in r)

        post_dir = output_dir / "p1"
        r = post_dir.file_contents("index.html")
        self.assertTrue('src="//example.com' in r)


class DirectoryTest(TestCase):
    def test_in_private(self):
        d = Directory(testdata.create_dir("/foo/_bar/che"))
        self.assertTrue(d.in_private())
        self.assertFalse(d.is_private())

        d = Directory(testdata.create_dir("/foo/_bar"))
        self.assertTrue(d.in_private())
        self.assertTrue(d.is_private())

