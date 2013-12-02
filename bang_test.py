from unittest import TestCase
import os

import testdata

from bang import Post

class PostTest(TestCase):
    def test_post(self):
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




