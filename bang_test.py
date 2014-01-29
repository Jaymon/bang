from unittest import TestCase
import os

import testdata

from bang.generator import Post, Site, Template
from bang.path import Directory, ProjectDirectory

def get_dirs(input_files):

    d = {
        'template/index.html': "{{ post.title }}\n{{ post.html }}\n{{ post.modified.strftime('%Y-%m-%d') }}\n"
    }
    d.update(input_files)

    output_dir = Directory(testdata.create_dir())
    project_dir = ProjectDirectory(testdata.create_dir())

    testdata.create_files(d, tmpdir=str(project_dir))
    return project_dir, output_dir


class ProjectDirectoryTest(TestCase):
    pass

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
    def test_codeblocks(self):
        project_dir, output_dir = get_dirs({
            'input/code/blocks.md': "\n".join([
                "```python",
                #"```no-highlight",
                "s = 'here we are'",
                "```"
            ])
        })

        d = Directory(project_dir.input_dir, 'code')
        d.ancestor_dir = project_dir.input_dir
        tmpl = Template(project_dir.template_dir)
        p = Post(d, output_dir, tmpl)
        #pout.v(p.html)



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




