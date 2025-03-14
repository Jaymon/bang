# -*- coding: utf-8 -*-
import os
import json
import re
import textwrap

import testdata

from bang.compat import *
from bang.md import Registry, Markdown
from . import TestCase


class MarkdownTest(TestCase):
    def test_find_priority(self):
        # https://python-markdown.github.io/extensions/api/#registry
        class Processor(object): pass

        reg = Registry()
        reg.register(Processor(), "foo", 10)
        reg.register(Processor(), "bar", 30)
        reg.register(Processor(), "che", 40)

        md = Markdown()

        pr = md.find_priority("<che", reg)
        self.assertEqual(45, pr)

        pr = md.find_priority(0, reg)
        self.assertEqual(0, pr)

        pr = md.find_priority(5, reg)
        self.assertEqual(5, pr)

        pr = md.find_priority(">bar", reg)
        self.assertEqual(25, pr)

        pr = md.find_priority(["<bar", ">che"], reg)
        self.assertEqual(35, pr)

        pr = md.find_priority("_end", reg)
        self.assertEqual(5, pr)

        pr = md.find_priority("_begin", reg)
        self.assertEqual(45, pr)

    def test_inline_html(self):
        p = self.get_page("before <code>```</code>, after")
        self.assertEqual("<p>before <code>```</code>, after</p>", p.html)

    def test_image_full_path(self):
        p = self.get_page('![this is the file](images/che.jpg)')
        self.assertRegexpMatches(
            p.html,
            r'//{}/[^/]+/images/che.jpg'.format(p.config.host)
        )

    def test_image_figure_only(self):
        p = self.get_page([
            "![this is the caption](foo.jpg)",
        ])
        r = p.html
        self.assertRegex(r, '<figure[^>]*><img alt="foo.jpg"')

    def test_image_figure_mixed(self):
        p = self.get_page([
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
        r = p.html
        self.assertRegex(r, '<figure[^>]*><img alt="foo.jpg"')
        self.assertTrue('<p>This text has an image <img alt="bar.jpg" ' in r)
        self.assertTrue('<p><img alt="che.jpg" ' in r)
        self.assertTrue('<p><img alt="baz.jpg" ' in r)

    def test_image_position(self):
        p = self.get_page('[![this is the alt](che.jpg "this is the title")](http://example.com)')
        r = p.html
        self.assertTrue("figure" in r)
        self.assertTrue("example.com" in r)
        self.assertTrue("figcaption" in r)
        self.assertTrue("img" in r)

        p = self.get_page({
            'che.jpg': "",
            'page.md': [
                '![this is the file](che.jpg)',
                ""
            ]
        })
        r = p.html
        self.assertTrue("figure" in r)
        self.assertTrue("figcaption" in r)

        p = self.get_page('![this is the file](che.jpg) and some text')
        r = p.html
        self.assertFalse("figure" in r)
        self.assertFalse("figcaption" in r)
        self.assertTrue("img" in r)
        self.assertTrue("title=" in r)

        p = self.get_page('and this has some text in front of the image ![this is the file](che.jpg)')
        r = p.html
        self.assertFalse("figure" in r)
        self.assertFalse("figcaption" in r)
        self.assertTrue("img" in r)
        self.assertTrue("title=" in r)

        p = self.get_page('all business in the front ![this is the file](che.jpg) and a party in the back')
        r = p.html
        self.assertFalse("figure" in r)
        self.assertFalse("figcaption" in r)
        self.assertTrue("img" in r)
        self.assertTrue("title=" in r)

    def test_image_title_alt(self):
        # alt = "alternate", title = ""
        p = self.get_page('![alternate](che.jpg "")')
        r = p.html
        self.assertTrue('title=""' in r)
        self.assertTrue('alt="alternate"' in r)

        # alt = "alternate", title = "image title"
        p = self.get_page('![alternate](che.jpg "image title")')
        r = p.html
        self.assertTrue('title="image title"' in r)
        self.assertTrue('alt="alternate"' in r)

        # alt = "alternate", title = None
        p = self.get_page('![alternate](che.jpg)')
        r = p.html
        self.assertTrue('title="alternate"' in r)
        self.assertTrue('alt="che.jpg"' in r)

        # alt = "", title = "image title"
        p = self.get_page('![](che.jpg "image title")')
        r = p.html
        self.assertTrue('title="image title"' in r)
        self.assertTrue('alt="che.jpg"' in r)

    def test_attr(self):
        p = self.get_page(
            ['![this is the file](che.jpg){: .centered }'],
            {'che.jpg': ""}
        )

        self.assertRegex(p.html, r'class=\"centered')

    def test_image_property(self):
        p = self.get_page(
            ['![this is the file](images/che.jpg)'],
            {'images/che.jpg': ""}
        )

        im = p.image
        self.assertTrue(im.endswith("images/che.jpg"))

        im = p.image
        self.assertTrue(im.endswith("images/che.jpg"))

    def test_image_lazyload(self):
        p = self.get_page([
            '![this is the file](images/che.jpg)',
            "",
            "images/che.jpg",
        ])

        p.output()
        html = p.output_file.read_text()
        self.assertEqual(2, html.count('loading="lazy"'))

    def test_href(self):
        p = self.get_page([
            "full [link](http://foo.com)",
            "full [path](/bar)",
            "file [path](che.txt)",
            "file [relative link](//bar.com)",
            ""
        ])

        html = p.html
        self.assertRegex(html, r'\"http://foo.com\"')
        self.assertRegex(html, rf'\"//{p.config.host}/bar\"')
        self.assertRegex(html, rf'\"{p.url}/che.txt\"')
        self.assertRegex(html, r'\"//bar.com\"')

    def test_codeblocks_1(self):
        p = self.get_page([
            "```python",
            #"```no-highlight",
            "s = 'here we are'",
            "```"
        ])

        self.assertRegex(p.html, r'<code class=\"codeblock python\">')

    def test_codeblocks_2(self):
        p = self.get_page([
            u'this is the post',
            u'',
            u'```python',
            u'def foo():',
            u'    pass',
            u'```',
            ''
        ])
        r = p.html
        self.assertRegex(r, r'class=\"codeblock python\"')

    def test_codeblocks_footnotes(self):
        markdown = textwrap.dedent("""
            before

            ```
            [I'm a reference-style link with text][reference text]

            [I'm a reference-style link with numbers][1]

            reference style link with [link text itself]

            [reference text]: https://www.mozilla.org "references can have titles also"
            [1]: http://slashdot.org
            [link text itself]: http://www.reddit.com
            ```

            after
            """)
        p = self.get_page(markdown)

        html = p.html
        for s in ["[reference text]: ", "[1]: ", "[link text itself]: "]:
            self.assertTrue(s in html)

    def test_easy_links(self):
        p = self.get_page([
            "[first][n]",
            "[n]: http://first.com",
            "",
            "[second][n]",
            "[n]: http://second.com",
            "",
            "[third][foo]",
            "[foo]: http://third.com",
        ])

        r = p.html
        for x in ["first", "second", "third"]:
            self.assertTrue(x in r)
            self.assertTrue("{}.com".format(x) in r)

    def test_link_titles(self):
        p = self.get_page([
            "[first][n]",
            "[n]: http://first.com \"this is the title\"",
        ])

        r = p.html
        self.assertTrue("this is the title" in r)

    def test_toc(self):
        p = self.get_page([
            "[TOC]",
            "# Header 1",
            "## Header 2",
            "### Header 3",
            "#### Header 4",
            "##### Header 5",
            "###### Header 6",
            "# Other Header 1",
        ])

        r = p.html
        self.assertTrue("toc" in r)
        self.assertTrue("#header-1" in r)
        self.assertTrue("#header-3" in r)
        self.assertTrue("#header-6" in r)
        self.assertTrue("#other-header-1" in r)
        for x in range(1, 7):
            self.assertTrue("h{}".format(x) in r)

        p = self.get_page([
            "# Header 1",
            "## Header 2",
            "### Header 3",
            "#### Header 4",
            "##### Header 5",
            "###### Header 6",
            "# Other Header 1",
        ])
        r = p.html
        self.assertFalse("toc" in r)

    def test_easy_footnotes(self):
        p = self.get_page([
            "first text[^n]",
            "[^n]: first footnote",
            "",
            "second text[^n]",
            "[^n]: second footnote",
            "",
            "third text[^foo]",
            "[^foo]: third footnote",
        ])

        r = p.html
        for x in ["1", "2", "foo"]:
            #self.assertTrue("#fn-2-{}".format(x) in r)
            #self.assertTrue("#fnref-2-{}".format(x) in r)
            self.assertRegexpMatches(r, "#fn-.+?-{}".format(x))
            self.assertRegexpMatches(r, "#fnref-.+?-{}".format(x))

    def test_uniq_footnotes(self):
        ps = self.get_pages({
            'uniq_footnotes_1/page.md': [
                "first text[^n]",
                "[^n]: first footnote",
            ],
            'uniq_footnotes_2/page.md': [
                "second text[^n]",
                "[^n]: second footnote",
            ],
            'uniq_footnotes_3/page.md': [
                "third text[^n]",
                "[^n]: third footnote",
            ]
        })

        uniqs = set()
        for i, p in enumerate(ps):
            r = p.html
            #m = re.search(r"#fn-[^\"]+", r)
            m = re.search(r"#fn-(\d+)", r)
            uniqs.add(m.group(1))

            m = re.search(r"#fnref-(\d+)", r)
            uniqs.add(m.group(1))

        self.assertEqual(3, len(uniqs))

    def test_ref_pos_fix(self):
        p = self.get_page([
            "[first][n] [text][n][^n] and [again][n]",
            "",
            "[n]: http://first.com",
            "[n]: http://one.com",
            "[^n]: first footnote",
            "[n]: http://again.com",
            "",
        ])
        r = p.html
        vals = [
            '<a href="http://first.com">first</a>',
            '<a href="http://one.com">text</a>',
            'href="#fn-',
            'href="#fnref-',
            'and <a href="http://again.com">again</a>',
        ]
        for v in vals:
            self.assertTrue(v in r, "{} NOT IN {}".format(v, r))

        p = self.get_page([
            "first text[^n] and [again][n]",
            "",
            "[^n]: first footnote",
            "second line of footnote",
            "[n]: http://again.com",
            "",
        ])
        r = p.html
        vals = [
            'href="#fn-',
            'href="#fnref-',
            'and <a href="http://again.com">again</a>',
        ]
        for v in vals:
            self.assertTrue(v in r, "{} NOT IN {}".format(v, r))


    def test_easy_images(self):
        p = self.get_page([
            "![foo title][n]",
            "[n]: foo.jpg",
        ])
        r = p.html
        self.assertTrue('alt="foo.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = self.get_page([
            "![foo title](foo.jpg)"
        ])
        r = p.html
        self.assertTrue('alt="foo.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = self.get_page([
            "![fooalt.jpg](foo.jpg \"foo title\")"
        ])
        r = p.html
        self.assertTrue('alt="fooalt.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = self.get_page([
            "![fooalt.jpg][n]",
            "[n]: foo.jpg \"foo title\"",
        ])
        r = p.html
        self.assertTrue('alt="fooalt.jpg"' in r)
        self.assertTrue('title="foo title"' in r)

        p = self.get_page([
            "![](foo.jpg)",
        ])
        r = p.html
        self.assertTrue('alt="foo.jpg"' in r)
        self.assertFalse('title' in r)

    def test_meta(self):
        p = self.get_page([
            "foo: bar",
            "tags: one, two, three",
            "",
            "This is the first sentence"
        ])

        r = p.html
        self.assertEqual("<p>This is the first sentence</p>", p.html)
        self.assertTrue("foo" in p.meta)

    def test_html_entities_codeblock(self):
        p = self.get_page([
            "```",
            "<b>This is html in a code block</b>",
            "```",
        ])

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


        p = self.get_page(body)

        r = p.html
        self.assertEqual(4, r.count("admonition-title"))

    def test_easy_footnotes_blockquote(self):
        vals = [
            '-1">1</a>',
            '-2">2</a>',
            '-3">3</a>',
        ]

        p = self.get_page([
            "before one[^n]",
            "",
            "[^n]: onefn",
            "",
            ">blockquote two[^n]",
            "",
            "[^n]: twofn",
            "",
            "after three[^n]",
            "",
            "[^n]: threefn",
        ])

        r = p.html
        for v in vals:
            self.assertTrue(v in r)

        p = self.get_page([
            "before one[^n]",
            "",
            "[^n] onefn",
            "",
        ])
        with self.assertRaises(RuntimeError):
            r = p.html

    def test_easy_links_blockquote(self):
        vals = [
            '<a href="http://one.com">one</a>',
            '<a href="http://two.com">two</a>',
            '<a href="http://three.com">three</a>',
        ]

        p = self.get_page([
            "before [one][n]",
            "",
            "[n]: http://one.com",
            "",
            ">blockquote [two][n]",
            "",
            "[n]: http://two.com",
            "",
            "after [three][n]",
            "",
            "[n]: http://three.com",
        ])

        r = p.html
        for v in vals:
            self.assertTrue(v in r)

        p = self.get_page([
            "before [one][n]",
            "",
            "[n]: http://one.com",
            "",
            "* [two][n]",
            "",
            "[n]: http://two.com",
            "",
            "after [three][n]",
            "",
            "[n]: http://three.com",
        ])

        r = p.html
        for v in vals:
            self.assertTrue(v in r)

        p = self.get_page([
            "before [one][n]",
            "",
            "[n] http://one.com",
            "",
        ])
        with self.assertRaises(RuntimeError):
            r = p.html

    def test_easy_footnote_inline_codeblock(self):
        p = self.get_page([
            "this is describing a `[^n]` ref and not declaring one",
            "",
            "describing a `[^n]` ref and has a ref[^n]",
            "",
            "[^n]: a ref",
        ])

        r = p.html
        self.assertEqual(2, r.count("<code>[^n]</code>"))

    def test_footnote_with_colon(self):
        p = self.get_page([
            "link before a [quote][n]:",
            "",
            "> quote",
            "",
            "footnote before a quote[^n]:",
            "",
            "> quote",
            "",
            "[n]: http://example.com",
            "[^n]: a ref",
        ])

        r = p.html
        self.assertTrue('<a href="http://example.com">quote</a>:' in r)
        self.assertTrue('</a></sup>:' in r)

    def test_mixed_blockquote(self):
        vals = [
            '<a href="http://one.com">one</a>',
            '<a href="http://two.com">two</a>',
            '<a href="http://three.com">three</a>',
            '-2">1</a>',
            '-4">2</a>',
            '-6">3</a>',
        ]

        p = self.get_page([
            "before [one][n][^n]",
            "",
            "[n]: http://one.com",
            "",
            "[^n]: onefn",
            "",
            ">blockquote [two][n][^n]",
            "",
            "[n]: http://two.com",
            "",
            "[^n]: twofn",
            "",
            "after [three][n][^n]",
            "",
            "[n]: http://three.com",
            ""
            "[^n]: threefn",
        ])

        r = p.html
        for v in vals:
            self.assertTrue(v in r)


class EmbedLocalPluginTest(TestCase):
    """Embed plugins that don't make any network requests or rely on any
    third party service requests"""
    def test_embed_link(self):
        p = self.get_page([
            "Before [text](http://bar.com) < and then there > after",
            "",
            "http://foo.com",
            "",
            "another [link **with** tags](http://che.com) text after",
        ])

        r = p.html
        self.assertTrue(
            '<a class="embed" href="http://foo.com">http://foo.com</a>' in r
        )
        self.assertEqual(1, r.count("embed"))

    def test_no_embed_link_in_codeblock(self):
        """Make sure link embedding doesn't work in codeblocks"""
        p = self.get_page([
            "```",
            "",
            "https://foo.com",
            "",
            "```",
        ])

        r = p.html
        self.assertFalse("embed" in r)

    def test_no_embed_twitter_links(self):
        p = self.get_page([
            "[@Jaymon](https://twitter.com/jaymon)",
        ])

        r = p.html
        self.assertTrue("a href" in r)

    def test_embed_vimeo(self):
        p = self.get_page([
            "before text",
            "",
            "https://vimeo.com/182739998",
            "",
            "after text",
        ])

        r = p.html
        self.assertEqual(1, r.count("<figure"))

    def test_embed_image(self):
        p = self.get_page({
            'bogus.jpg': "",
            'page.md': [
                "before text",
                "",
                "bogus.jpg",
                "",
                "after text",
            ],
        })

        r = p.html
        self.assertTrue('alt="bogus.jpg"' in r)
        self.assertTrue('title=""' in r)

    def test_embed_image_url(self):
        p = self.get_page({
            'bogus.jpg': "",
            'page.md': [
                "before text",
                "",
                "http://embedded.com/full/url/bogus.jpg",
                "",
                "after text",
            ],
        })

        r = p.html
        self.assertTrue('alt="bogus.jpg"' in r)
        self.assertTrue('title=""' in r)
        self.assertTrue('src="http://embedded.com/full/url/bogus.jpg"' in r)

    def test_embed_youtube_1(self):
        p = self.get_page([
            "before",
            "",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "",
            "after",
        ])

        r = p.html
        self.assertTrue("<figure" in r)

    def test_embed_youtube_2(self):
        p = self.get_page(
            "12 notes, that's all you get! These 12 notes give us everything"
            " from [Beethoven's 5th symphony]"
            "(https://www.youtube.com/watch?v=_4IRMYuE1hI)"
            " to [Hanson's MMMBop]"
            "(https://www.youtube.com/watch?v=NHozn0YXAeE),"
            "and everything in between. They all use the same set of 12 notes"
        )

        r = p.html
        self.assertFalse("<iframe" in r)


class EmbedRemotePluginTest(TestCase):
    """Emboed plugins that make requests"""
    def setUp(self):
        """This makes sure these tests only run when they are run specifically,
        so these will be skipped when all tests are run, we do this because
        these tests can ping external networks"""
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

    def test_embed_twitter(self):
        p = self.get_page(
            {
                "page.md": [
                    "before",
                    "",
                    "https://twitter.com/JohnKirk/status/801086441325375491",
                    "",
                    "middle",
                    "",
                    "https://twitter.com/foo/status/100",
                    "",
                    "after",
                ],
                "_embed/twitter.json": json.dumps({
                    "https://twitter.com/foo/status/100": {
                        'html': (
                            '<blockquote class="twitter-tweet">'
                            '<p lang="en" dir="ltr">foo</p>'
                            '&mdash;'
                            ' <a href="https://twiiter.com/foo/status/100">'
                            'month DD, YYYY</a>'
                            '</blockquote>'
                        ),
                    },
                })
            }
        )

        r = p.html
        self.assertEqual(2, r.count("<figure"))

        contents = json.loads(
            p.input_dir.child_dir("_embed").file_bytes("twitter.json")
        )
        self.assertEqual(2, len(contents))

        foo_html = contents["https://twitter.com/foo/status/100"]["html"]
        self.assertTrue("month DD, YYYY" in foo_html)

