# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import testdata

from bang.compat import *
from bang.path import Directory, File, Image
from . import TestCase


class DirectoryTest(TestCase):
    def test_relative_parts(self):
        d = Directory("/foo/bar/che/bam/boo")
        p = d.relative_parts("/")
        self.assertEqual(["foo", "bar", "che", "bam", "boo"], p)

        p = d.relative_parts("/foo/bar/")
        self.assertEqual(["che", "bam", "boo"], p)

    def test_copy_paths_all(self):
        output_dir = testdata.create_dir()
        input_dir = Directory(testdata.create_files({
            "foo.txt": "",
            "bar/che.txt": "",
            "boo/baz/bah.txt": ""
        }))

        s = set([input_dir.basename, "bar", "boo", "baz"])

        for isd, osd in input_dir.copy_paths(output_dir):
            self.assertTrue(isd.basename in s, "{} not in s".format(isd.basename))
            #self.assertTrue(osd.basename in s)
            s.discard(isd.basename)

        self.assertEqual(0, len(s))

    def test_copy_paths_depth(self):
        output_dir = testdata.create_dir()
        input_dir = Directory(testdata.create_files({
            "foo.txt": "",
            "bar/che.txt": "",
            "boo/baz/bah.txt": ""
        }))

        self.assertEqual(1, len(list(input_dir.copy_paths(output_dir, depth=1))))
        self.assertEqual(3, len(list(input_dir.copy_paths(output_dir, depth=2))))
        self.assertEqual(4, len(list(input_dir.copy_paths(output_dir, depth=3))))
        self.assertEqual(4, len(list(input_dir.copy_paths(output_dir, depth=0))))

    def test_copy_to(self):
        output_dir = Directory(testdata.create_dir())
        input_dir = Directory(testdata.create_files({
            "foo.txt": "",
            "bar/che.txt": "",
            "boo/baz/bah.txt": ""
        }))

        ifs = input_dir.files(depth=0)
        ofs = output_dir.files(depth=0)
        self.assertNotEqual(len(ifs), len(ofs))

        input_dir.copy_to(output_dir)
        ifs = input_dir.files(depth=0)
        ofs = output_dir.files(depth=0)
        self.assertEqual(len(ifs), len(ofs))

    def test_directories(self):
        d = Directory(testdata.create_files({
            "foo.txt": "",
            "bar/che.txt": "",
            "boo/baz/bah.txt": ""
        }))

        ds = [v.path for v in d.directories(depth=0)]
        self.assertEqual(3, len(ds))

        ds = [v.path for v in d.directories(depth=1)]
        self.assertEqual(2, len(ds))

    def test_files_1(self):
        d = Directory(testdata.create_files({
            "foo.txt": "",
            "bar/che.txt": "",
            "boo/baz/bah.txt": ""
        }))

        fs = [v for v in d.files(depth=0)]
        self.assertEqual(3, len(fs))

        fs = [v for v in d.files(depth=1)]
        self.assertEqual(1, len(fs))

    def test_files_2(self):
        d = Directory(testdata.create_files({
            "foo.txt": "",
            "che.txt": "",
            "bah.txt": ""
        }))

        fs = d.files()
        self.assertEqual(3, len(d.files()))

        fs2 = d.files(regex=r"^che")
        self.assertEqual(1, len(fs2))
        self.assertTrue(fs2[0].endswith("che.txt"))

        fs2 = d.files(regex=r"^che", exclude=True)
        self.assertEqual(2, len(fs2))
        for f in fs2:
            self.assertFalse(f.endswith("che.txt"))

    def test_in_private(self):
        d = Directory(testdata.create_dir("/foo/_bar/che"))
        self.assertTrue(d.in_private())
        self.assertFalse(d.is_private())

        d = Directory(testdata.create_dir("/foo/_bar"))
        self.assertTrue(d.in_private())
        self.assertTrue(d.is_private())

    def test_has_file(self):
        f = testdata.create_file("/foo/bar/che/index.html")

        d = Directory(f.parent)
        self.assertTrue(d.has_file("index.html"))

        d = Directory(f.parent.parent)
        self.assertTrue(d.has_file("che", "index.html"))

        d = Directory(f.parent.parent.parent)
        self.assertTrue(d.has_file("bar", "che", "index.html"))


class FileTest(TestCase):
    def test___init__(self):
        path = testdata.create_file("/foo/bar/che/index.html")
        f = File(path.basedir, "foo", "bar", "che", "index.html")
        self.assertTrue(path, f.path)

    def test_create(self):
        contents = "contents"
        d = Directory(testdata.create_dir())
        d.create_file("foo/test.txt", contents)
        f = File(d.path, "foo", "test.txt")
        self.assertTrue(f.exists())

        s = f.contents()
        self.assertEqual(contents, s)


class ImageTest(TestCase):
    def test_dimensions(self):
        ts = [
            ("agif", (11, 29)),
            ("gif", (190, 190)),
            ("jpg", (190, 190)),
            ("png", (190, 190)),
            ("ico", (64, 64)),
        ]

        for t in ts:
            im = Image(testdata.create_image(t[0]))
            self.assertEqual(t[1], im.dimensions)

    def test_is_animated(self):
        im = Image(testdata.create_animated_gif())
        self.assertTrue(im.is_animated())

        im = Image(testdata.create_gif())
        self.assertFalse(im.is_animated())

        im = Image(testdata.create_jpg())
        self.assertFalse(im.is_animated())


