from unittest import TestCase
import os
import codecs

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

    d = {
        'template/index.html': "{{ post.title }}\n{{ post.html }}\n{{ post.modified.strftime('%Y-%m-%d') }}\n"
    }
    d.update(input_files)

    output_dir = Directory(testdata.create_dir())
    project_dir = ProjectDirectory(testdata.create_dir())

    testdata.create_files(d, tmpdir=str(project_dir))
    return project_dir, output_dir

def get_post(post_files, name=""):
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
    for rp in ["bangfile.py"]:
        if rp in post_files:
            di[rp] = post_files.pop(rp)

    for basename, file_contents in post_files.items():
        fp = os.path.join('input', name, basename)
        di[fp] = file_contents

    project_dir, output_dir = get_dirs(di)
    d = Directory(project_dir.input_dir, name)
    d.ancestor_dir = project_dir.input_dir
    tmpl = Template(project_dir.template_dir)
    p = Post(d, output_dir, tmpl, Config(project_dir))
    return p


class PluginTest(TestCase):
    def test_indexone(self):
        from bang.plugins import indexone
        project_dir, output_dir = get_dirs({
            'input/1/one.md': u'1. {}'.format(testdata.get_unicode_words()),
        })
        s = Site(project_dir, output_dir)
        s.output()
        self.assertTrue(s.output_dir.has_file('index.html'))

        # make sure it doesn't generate the file if index already exists
        project_dir, output_dir = get_dirs({
            'input/1/one.md': u'1. {}'.format(testdata.get_unicode_words()),
            'input/index.txt':u'2. {}'.format(testdata.get_unicode_words()),
        })
        s = Site(project_dir, output_dir)
        s.output()
        self.assertFalse(s.output_dir.has_file('index.html'))

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
        output_dir = Directory(testdata.create_dir())
        project_dir = ProjectDirectory(testdata.create_dir())
        testdata.create_files(
            {
                'input/aux/index.md': testdata.get_unicode_words(),
                'template/index.html': "{{ post.title }}\n{{ post.html }}\n{{ post.modified.strftime('%Y-%m-%d') }}\n"
            },
            tmpdir=str(project_dir)
        )

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

    def test_image(self):
        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '[![this is the alt](che.jpg this is the title)](http://example.com)',
                ""
            ])
        })
        self.assertRegexpMatches(p.html, '<p\s+class=\"image-centered\"')

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![this is the file](che.jpg)',
                ""
            ])
        })
        self.assertRegexpMatches(p.html, 'class=\"image-centered\"')

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                '![this is the file](che.jpg) and some text',
                ""
            ])
        })
        self.assertRegexpMatches(p.html, 'class=\"image-floating\"')

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                'and this has some text in front of the image ![this is the file](che.jpg)',
                ""
            ])
        })
        self.assertRegexpMatches(p.html, 'class=\"image-floating\"')

        p = get_post({
            'che.jpg': "",
            'foo.md': "\n".join([
                'all business in the front ![this is the file](che.jpg) and a party in the back',
                ""
            ])
        })
        self.assertRegexpMatches(p.html, 'class=\"image-floating\"')

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
            ])
        })

        r = p.html
        pout.v(r)

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


class SkeletonTest(TestCase):
    def test_generate(self):
        project_dir = ProjectDirectory(testdata.create_dir())
        s = skeleton.Skeleton(project_dir)
        s.output()

        for file_dict in skeleton.file_skeleton:
            d = project_dir / file_dict['dir']
            self.assertTrue(d.exists())
            self.assertTrue(os.path.isfile(os.path.join(str(d), file_dict['basename'])))

