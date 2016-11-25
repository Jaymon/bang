from unittest import TestCase
import os
import codecs
import sys
import json

import testdata

from bang.generator import Post, Site, Template, Config
from bang.path import Directory, ProjectDirectory
from bang import skeleton
from bang import echo


# configure root logger
# import logging
# import sys
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# log_handler = logging.StreamHandler(stream=sys.stderr)
# log_formatter = logging.Formatter('[%(levelname)s] %(message)s')
# log_handler.setFormatter(log_formatter)
# logger.addHandler(log_handler)


# turn on all logging for the tests
echo.quiet = False


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


def get_post(post_files, name=""):

    # clear the environment
    for k, v in os.environ.items():
        if k.startswith('BANG_'):
            del os.environ[k]
    sys.modules.pop("bangfile_module", None)

    if not name:
        name = testdata.get_ascii(16)

    di = {
        'bangfile.py': "\n".join([
            "host = 'example.com'",
            "name = 'example site'",
            ""
        ])
    }

    # replace any project files if they are present
    for rp in di.keys():
        if rp in post_files:
            di[rp] = post_files.pop(rp)

    for basename, file_contents in post_files.items():
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

    return s.posts.first_post if len(s.posts) else s.auxs.first_post


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


class PostTest(TestCase):
    def test_no_bangfile_host(self):
        name = testdata.get_ascii(16)
        p = get_post({
            'foo.md': "\n".join([
                "hi"
            ]),
            'bangfile.py': ""
        }, name=name)

        self.assertEqual("/{}".format(name), p.url)

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

    def test_easy_footers(self):
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
            self.assertTrue("#fn-2-{}".format(x) in r)
            self.assertTrue("#fnref-2-{}".format(x) in r)

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
        self.assertTrue("<figure>" in r)

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
        self.assertEqual(2, r.count("<figure>"))

        contents = json.loads(p.directory.file_contents("twitter.json"))
        self.assertEqual(2, len(contents))

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
        pout.v(r, p)


class SkeletonTest(TestCase):
    def test_generate(self):
        project_dir = ProjectDirectory(testdata.create_dir())
        s = skeleton.Skeleton(project_dir)
        s.output()

        for file_dict in skeleton.file_skeleton:
            d = project_dir / file_dict['dir']
            self.assertTrue(d.exists())
            self.assertTrue(os.path.isfile(os.path.join(str(d), file_dict['basename'])))

