# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

import testdata

from bang.types import Post, Aux, Directories
from . import TestCase
from . import get_body, get_dirs, get_posts, get_post


class DirectoriesTest(TestCase):
    def test_pages(self):
        s = self.get_site({})
        posts = Directories(s)
        for x in range(29):
            p = Post(s.input_dir, s.output_dir, s)
            #p.body = x
            posts.append(p)

        r = []
        for ps in posts.pages(10):
            r.append(ps)

        for i, total in enumerate([10, 10, 9]):
            self.assertEqual(total, len(r[i]))

        r = []
        for ps in posts.pages(10, reverse=True):
            r.append(ps)

        for i, total in enumerate([10, 10, 9]):
            self.assertEqual(total, len(r[i]))

    def test_paginated_output(self):
        posts = self.get_count_posts(21)

        posts.output()
        self.assertTrue(posts.site.output_dir.has_file("index.html"))
        self.assertTrue(posts.site.output_dir.child("page", "2").has_file("index.html"))
        self.assertTrue(posts.site.output_dir.child("page", "3").has_file("index.html"))
        self.assertFalse(posts.site.output_dir.child("page", "4").has_file("index.html"))


class PostTest(TestCase):
    def test_no_bangfile_host(self):
        name = testdata.get_ascii(16)
        ps = self.get_posts({
            '{}/foo.md'.format(name): "\n".join([
                "hi"
            ]),
            'bangfile.py': ""
        })

        self.assertRegexpMatches(ps.first_post.url, "^/{}$".format(name))

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
        p = self.get_post(
            ['![this is the file](che.jpg){: .centered }'],
            {'che.jpg': ""}
        )

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

    def test_link_titles(self):
        p = get_post({
            'link_titles_1.md': "\n".join([
                "[first][n]",
                "[n]: http://first.com \"this is the title\"",
            ])
        })

        r = p.html
        self.assertTrue("this is the title" in r)

    def test_toc(self):
        p = get_post({
            'toc_1.md': [
                "[TOC]",
                "# Header 1",
                "## Header 2",
                "### Header 3",
                "#### Header 4",
                "##### Header 5",
                "###### Header 6",
                "# Other Header 1",
            ]
        })

        r = p.html
        self.assertTrue("toc" in r)
        self.assertTrue("#header-1" in r)
        self.assertTrue("#header-3" in r)
        self.assertTrue("#header-6" in r)
        self.assertTrue("#other-header-1" in r)
        for x in range(1, 7):
            self.assertTrue("h{}".format(x) in r)

        p = get_post({
            'toc_2.md': [
                "# Header 1",
                "## Header 2",
                "### Header 3",
                "#### Header 4",
                "##### Header 5",
                "###### Header 6",
                "# Other Header 1",
            ]
        })
        r = p.html
        self.assertFalse("toc" in r)

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
            self.assertRegexpMatches(r, "#fn-.+?-{}".format(x))
            self.assertRegexpMatches(r, "#fnref-.+?-{}".format(x))

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
            #m = re.search(r"#fn-[^\"]+", r)
            m = re.search(r"#fn-(\d+)", r)
            uniqs.add(m.group(1))

            m = re.search(r"#fnref-(\d+)", r)
            uniqs.add(m.group(1))

        self.assertEqual(3, len(uniqs))

    def test_ref_pos_fix(self):
        p = get_post({'ref_pos_fix_1.md': [
            "[first][n] [text][n][^n] and [again][n]",
            "",
            "[n]: http://first.com",
            "[n]: http://one.com",
            "[^n]: first footnote",
            "[n]: http://again.com",
            "",
        ]})
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

        p = get_post({'ref_pos_fix_2.md': [
            "first text[^n] and [again][n]",
            "",
            "[^n]: first footnote",
            "second line of footnote",
            "[n]: http://again.com",
            "",
        ]})
        r = p.html
        vals = [
            'href="#fn-',
            'href="#fnref-',
            'and <a href="http://again.com">again</a>',
        ]
        for v in vals:
            self.assertTrue(v in r, "{} NOT IN {}".format(v, r))


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

    def test_easy_footnotes_blockquote(self):
        vals = [
            '-1">1</a>',
            '-2">2</a>',
            '-3">3</a>',
        ]

        p = get_post({
            'fn_bq_1.md': [
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
            ]
        })

        r = p.html
        for v in vals:
            self.assertTrue(v in r)

        p = get_post({'fn_bq_2.md': [
            "before one[^n]",
            "",
            "[^n] onefn",
            "",
        ]})
        with self.assertRaises(RuntimeError):
            r = p.html

    def test_easy_links_blockquote(self):
        vals = [
            '<a href="http://one.com">one</a>',
            '<a href="http://two.com">two</a>',
            '<a href="http://three.com">three</a>',
        ]

        p = get_post({
            'link_bq_1.md': [
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
            ]
        })

        r = p.html
        for v in vals:
            self.assertTrue(v in r)

        p = get_post({
            'link_bq_2.md': [
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
            ]
        })

        r = p.html
        for v in vals:
            self.assertTrue(v in r)

        p = get_post({'link_bq_3.md': [
            "before [one][n]",
            "",
            "[n] http://one.com",
            "",
        ]})
        with self.assertRaises(RuntimeError):
            r = p.html

    def test_easy_footnote_inline_codeblock(self):
        p = self.get_post([
            "this is describing a `[^n]` ref and not declaring one",
            "",
            "describing a `[^n]` ref and has a ref[^n]",
            "",
            "[^n]: a ref",
        ])

        r = p.html
        self.assertEqual(2, r.count("<code>[^n]</code>"))

    def test_footnote_with_colon(self):
        p = self.get_post([
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

        p = get_post({'mixed_bq_1.md': [
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
        ]})

        r = p.html
        for v in vals:
            self.assertTrue(v in r)


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

