# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import sys
import re
from distutils import dir_util
import shutil
import codecs
import logging
from jinja2 import Environment, FileSystemLoader
import fnmatch


from .compat import *


logger = logging.getLogger(__name__)


class Path(object):
    """Parent class containing common methods for File and Directory"""

    @property
    def basename(self):
        return os.path.basename(self.path)

    def __init__(self, *bits):
        self.path = ''
        self.ancestor_dir = None
        if bits:
            bits = list(String(b) for b in bits)
            bits[0] = self.normalize(bits[0])
            for i in xrange(1, len(bits)):
                bits[i] = bits[i].strip('\\/')
            self.path = os.path.join(*bits)

    @classmethod
    def normalize(cls, d):
        """completely normalize a relative path (a path with ../, ./, or ~/)"""
        return os.path.abspath(os.path.expanduser(str(d)))

    def __str__(self):
        return ByteString(self.path) if is_py2 else self.__unicode__()

    def __unicode__(self):
        return String(self.path)

    def is_private(self):
        basename = self.basename
        return basename.startswith('_')

    def in_private(self):
        """make sure this path isn't an any private directory"""
        ret = False
        path = self.path
        while path:
            path, basename = os.path.split(path)
            if basename.startswith('_'):
                ret = True
                break
        return ret

    def relative(self, ancestor_dir=None):
        """
        returns the relative bits to the parent_dir

        :Example:
            d = Directory("/foo/bar/baz/che")
            d.relative("/foo/bar") # baz/che
            d.relative("/foo") # bar/baz/che

        :param ancestor_dir: string|Directory, the directory you want to return that self
            is a child of, if ancestor_dir is empty then it will use self.ancestor_dir
        :returns: string, the part of the path that is relative
        """
        if not ancestor_dir:
            ancestor_dir = self.ancestor_dir
        if not ancestor_dir:
            raise ValueError("no ancestor_dir found")

        relative = self.path.replace(String(ancestor_dir), '').strip(os.sep)
        return relative

    def clone(self):
        """return a new instance with the same path"""
        d = type(self)(self.path)
        d.ancestor_dir = self.ancestor_dir
        return d


class File(Path):

    @property
    def ext(self):
        """return the extension of the file, the basename without the fileroot"""
        return os.path.splitext(self.basename)[1]

    @property
    def fileroot(self):
        """return the basename without the extension"""
        return os.path.splitext(self.basename)[0]

    def exists(self):
        return os.path.isfile(self.path)

    def contents(self, encoding="UTF-8"):
        contents = ""
        try:
            with codecs.open(self.path, encoding=encoding, mode='r+') as f:
                contents = f.read()
        except IOError:
            # ignore file does not exist errors
            pass

        return contents

    def create(self, contents, binary=False, encoding="UTF-8"):
        """create the file with basename in this directory with contents"""
        logger.debug("create file {}".format(output_file))

        oldmask = os.umask(0)

        if binary:
            # https://docs.python.org/2.7/library/functions.html#open
            f = open(self.path, mode="w+b")

        else:
            f = codecs.open(self.path, encoding=encoding, mode='w+')
            f.truncate(0)
            f.seek(0)

        f.write(contents)
        f.close()
        oldmask = os.umask(oldmask)
        return self

    def copy_to(self, output_dir):
        basename = self.basename
        output_file = File(output_dir, basename)
        logger.debug("copy file {} to {}".format(self.path, output_file))
        return File(shutil.copy(String(self.path), String(output_file)))


class Image(File):
    @property
    def dimensions(self):

        import struct
        import imghdr

        with open(self.path, 'rb') as fp:
            head = fp.read(24)
            if len(head) != 24:
                return 0, 0

            what = imghdr.what(None, head)

            if what == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    return 0, 0

                width, height = struct.unpack('>ii', head[16:24])

            elif what == 'gif':
                width, height = struct.unpack('<HH', head[6:10])

            elif what == 'jpeg':
                try:
                    fp.seek(0) # Read 0xff next
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf or ftype in (0xc4, 0xc8, 0xcc):
                        fp.seek(size, 1)
                        byte = fp.read(1)
                        while ord(byte) == 0xff:
                            byte = fp.read(1)
                        ftype = ord(byte)
                        size = struct.unpack('>H', fp.read(2))[0] - 2
                    # We are at a SOFn block
                    fp.seek(1, 1)  # Skip `precision' byte.
                    height, width = struct.unpack('>HH', fp.read(4))
                except Exception: #IGNORE:W0703
                    return

            else:
                return

            return width, height


class Directory(Path):

    def exists(self):
        return os.path.isdir(self.path)

    def file_contents(self, basename):
        """return the contents of the basename file in this directory"""
        contents = ""
        output_file = File(self.path, basename)
        return output_file.contents()

    def create_file(self, basename, contents, binary=False):
        """create the file with basename in this directory with contents"""
        output_file = File(self.path, basename)
        return output_file.create(contents, binary=binary)

    def copy_file(self, input_file):
        """copy the input_file to this directory"""
        return File(input_file).copy_to(self.path)

    def copy_paths(self, output_dir):
        """you have current directory self and you want to copy the entire directory
        tree of self into output_dir, this finds all the subdirectories of self and
        creates an equivalent path in output_dir

        :param output_dir: Directory, the directory you want to copy the tree of this
            Directory (self) into
        :returns: yields tuples of (input_subdir, output_subdir)
        """
        input_dir = self.clone()
        input_dir.ancestor_dir = self
        output_dir = Directory(output_dir).clone()
        yield input_dir, output_dir

        for input_subdir in input_dir:
            output_subdir = output_dir / input_subdir.relative()
            yield input_subdir, output_subdir

    def copy_to(self, output_dir):
        """Copies the entire tree of self to output_dir

        :param output_dir: Directory, the directory you want to copy the tree of this
            Directory (self) into
        """
        for input_subdir, output_subdir in self.copy_paths(output_dir):
            #if input_subdir.is_private(): continue
            output_subdir.create()
            for f in input_subdir.files():
                output_subdir.copy_file(f)

    def create(self):
        """create the directory path"""
        logger.debug("create dir: {}".format(self.path))
        # https://docs.python.org/2.5/dist/module-distutils.dirutil.html
        return dir_util.mkpath(self.path)

    def clear(self):
        """this will clear a directory path of all files and folders"""
        # http://stackoverflow.com/a/1073382/5006
        logger.debug("clearing {}".format(self.path))
        dir_util.mkpath(self.path)
        for root, dirs, files in os.walk(self.path, topdown=True):
            for td in dirs:
                shutil.rmtree(os.path.join(root, td))

            for tf in files:
                os.unlink(os.path.join(root, tf))

            break

        # clear dir_util's internal cache otherwise calling create() again in same run
        # won't actually create the directory and won't tell you it didn't create it and
        # there doesn't seem to be an "official" way to clear the cache
        # https://hg.python.org/cpython/file/2.7/Lib/distutils/dir_util.py#l14
        dir_util._path_created = {}
        return True

    def child(self, *bits):
        """Return a new instance with bits added onto self's path"""
        return Directory(self.path, *bits)

    def __div__(self, bits):
        if isinstance(bits, basestring):
            bits = [bits]
        else:
            bits = list(bits)
        return self.child(*bits)

    def __truediv__(self, bits):
        return self.__div__(bits)

    def __iter__(self):
        for d in self.directories(depth=0):
            yield d

    def files(self, regex=None, depth=1, exclude=False):
        """return files in self

        :param regex: string, the regular expression
        :param depth: int, if 1, just return immediate files, if 0 return all files
            of the entire tree, otherwise just return depth files
        :param exclude: bool, if True then any files that would be returned won't
            and files that wouldn't be returned normally will be
        :returns: list, the matching files
        """
        fs = []
        for root_dir, subdirs, files in os.walk(self.path, topdown=True):
            for basename in files:
                if not basename.startswith('_'):
                    if exclude:
                        if regex and not re.search(regex, basename, re.I):
                            fs.append(os.path.join(root_dir, basename))

                    else:
                        if not regex or re.search(regex, basename, re.I):
                            fs.append(os.path.join(root_dir, basename))


            fs.sort()
            if depth != 1:
                fs2 = []
                depth = depth - 1 if depth else depth
                for sd in subdirs:
                    d = Directory(root_dir, sd)
                    if not d.is_private():
                        fs2.extend(d.files(regex=regex, depth=depth))
                fs.extend(fs2)

            break

        return fs

    def directories(self, regex=None, depth=1):
        """return directories in self

        :param regex: string, the regular expression
        :param depth: int, if 1, just return immediate dirs, if 0 return all subdirs
            of the entire tree, otherwise just return depth dirs
        :returns: list, the matching directories
        """
        ds = []
        for root_dir, dirs, _ in os.walk(self.path, topdown=True):
            for basename in dirs:
                if not regex or re.search(regex, basename, re.I):
                    d = Directory(root_dir, basename)
                    d.ancestor_dir = self
                    if not d.is_private():
                        ds.append(d)

            ds.sort(key=lambda d: d.path)
            if depth != 1:
                ds2 = []
                depth = depth - 1 if depth else depth
                for d in ds:
                    for sd in d.directories(regex=regex, depth=depth):
                        sd.ancestor_dir = self
                        ds2.append(sd)

                ds.extend(ds2)

            break

        return ds

    def has_file(self, *bits):
        """return true if the file basename exists in this directory"""
        return File(self.path, *bits).exists()

    def has_directory(self, *bits):
        d = self.child(*bits)
        return d.exists()

    def has_index(self):
        """returns True if this directory has an index.* file already"""
        r = False
        for f in self.files(r'^index\.'):
            r = True
            break

        return r


class DataDirectory(Directory):
    def __init__(self):
        base_dir = os.path.dirname(sys.modules[__name__.split(".")[0]].__file__)
        super(DataDirectory, self).__init__(base_dir, "data")

    def themes_dir(self):
        return self.child("themes")


class TemplateDirectory(object):
    """Thin wrapper around Jinja functionality that handles templating things

    http://jinja.pocoo.org/docs/dev/
    """
    def __init__(self, template_dir):
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(String(template_dir)),
            #extensions=['jinja2.ext.with_'] # http://jinja.pocoo.org/docs/dev/templates/#with-statement
        )

        self.templates = {}
        for f in fnmatch.filter(os.listdir(String(self.template_dir)), '*.html'):
            filename, fileext = os.path.splitext(f)
            self.templates[filename] = f

    def has(self, template_name):
        return template_name in self.templates

    def output(self, template_name, filepath, config, **kwargs):
        """output kwargs using the template template_name to filepath

        :param template_name: string, the template you want to use for kwargs
        :param filepath: string, the destination file that will be output to
        :param config: Config instance
        :param **kwargs: dict, all these will be passed to the template
        """
        tmpl = self.env.get_template("{}.html".format(template_name))
        return tmpl.stream(config=config, **kwargs).dump(filepath, encoding=config.encoding)


