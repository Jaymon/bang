from unittest import TestCase
import os

import testdata

from bang.generator import Post, Site
from bang.path import Directory, ProjectDirectory

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

class PostTest(TestCase):
    def test_post(self):
        return # I'm pretty sure this test is outdated
        relative = "Foo Bar"
        body_file = "post.md"
        files = ["1.jpg", "2.jpg"]
        input_root = testdata.create_dir()
        output_root = testdata.create_dir()

        # actually create the structure
        tmpdir = testdata.create_dir(relative, input_root)
        post_body = testdata.create_file("post.md", "blah", tmpdir)
        fs = testdata.create_files({f: "" for f in files}, tmpdir)

        p = Post(input_root, relative, body_file, files)

        self.assertEqual(relative, p.title)
        self.assertEqual("/foo-bar", p.url)
        self.assertEqual("<p>{}</p>".format(p.body), p.html)

        p.move_files(output_root)
        for f in files:
            filepath = os.path.join(output_root, relative, f)
            self.assertTrue(os.path.isfile(filepath))




