import os
import re
from distutils import dir_util
import shutil
import types
import codecs
import logging


logger = logging.getLogger(__name__)


class Directory(object):

    #content_file_regex = ur'\.(md|html|txt|markdown)$'
    content_file_regex = ur'\.(md|markdown)$'

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def content_file(self):
        for f in self.files(self.content_file_regex):
            break
        return f

    @property
    def other_files(self):
        for f in self.files():
            if not re.search(self.content_file_regex, f, re.I):
                yield f

    def __init__(self, *bits):
        self.path = ''
        self.ancestor_dir = None
        if bits:
            bits = list(bits)
            bits[0] = self.normalize(bits[0])
            for i in xrange(1, len(bits)):
                bits[i] = bits[i].strip('\\/')
            self.path = os.path.join(*bits)

    @classmethod
    def normalize(cls, d):
        """completely normalize a relative path (a path with ../, ./, or ~/)"""
        return os.path.abspath(os.path.expanduser(str(d)))

    def exists(self):
        return os.path.isdir(self.path)

    def file_contents(self, basename):
        """return the contents of the basename file in this directory"""
        contents = ""
        output_file = os.path.join(self.path, basename)
        try:
            with codecs.open(output_file, encoding='utf-8', mode='r+') as f:
                contents = f.read()
        except IOError:
            # ignore file does not exist errors
            pass

        return contents

    def create_file(self, basename, contents, binary=False):
        """create the file with basename in this directory with contents"""
        output_file = os.path.join(self.path, basename)
        logger.debug("create file {}".format(output_file))

        oldmask = os.umask(0)

        if binary:
            # https://docs.python.org/2.7/library/functions.html#open
            f = open(output_file, mode="w+b")

        else:
            f = codecs.open(output_file, encoding='utf-8', mode='w+')
            f.truncate(0)
            f.seek(0)

        f.write(contents)
        f.close()
        oldmask = os.umask(oldmask)

        return output_file

    def copy_file(self, input_file):
        """copy the input_file to this directory"""
        basename = os.path.basename(input_file)
        output_file = os.path.join(self.path, basename)
        logger.debug("copy file {} to {}".format(input_file, output_file))
        return shutil.copy(input_file, output_file)

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

    def __div__(self, bits):
        if isinstance(bits, types.StringTypes):
            bits = [bits]
        else:
            bits = list(bits)

        return Directory(self.path, *bits)

    def __truediv__(self, bits):
        return self.__div__(bits)

    def __str__(self):
        return self.path

    def __unicode__(self):
        return unicode(self.path)

    def __iter__(self):
        for root_dir, dirs, _ in os.walk(self.path, topdown=True):
            dirs[:] = [d for d in dirs if not d.startswith("_")]
            dirs.sort()
            for basename in dirs:
                d = Directory(root_dir, basename)
                d.ancestor_dir = self
                yield d

    def files(self, regex=None):
        fs = []
        for root_dir, _, files in os.walk(self.path, topdown=True):
            for basename in files:
                if basename.startswith('_'): continue
                if regex and not re.search(regex, basename, re.I):
                    continue
                fs.append(os.path.join(root_dir, basename))
            break

        return fs

    def has_file(self, basename):
        """return true if the file basename exists in this directory"""
        return os.path.isfile(os.path.join(str(self), basename))

    def has_index(self):
        """returns True if this directory has an index.* file already"""
        r = False
        for f in self.files(ur'^index.'):
            r = True
            break

        return r

    def is_post(self):
        """return true if this directory has a blog post in it"""
        return not self.is_aux() and self.files(self.content_file_regex)

    def is_aux(self):
        """return True if this is a directory with an index.* file in it"""
        ret_bool = False
        if self.files(ur'^index{}'.format(self.content_file_regex)):
            ret_bool = True

        return ret_bool

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

        example --
            d = Directory("/foo/bar/baz/che")
            d.relative("/foo/bar") # baz/che
            d.relative("/foo") # bar/baz/che

        ancestor_dir -- string|Directory -- the directory you want to return that self
            is a child of, if parent_dir is empty than it will use self.ancestor_dir
        return -- string -- the part of the path that is relative
        """
        if not ancestor_dir:
            ancestor_dir = self.ancestor_dir
        assert ancestor_dir, "no ancestor_dir found"

        relative = self.path.replace(str(ancestor_dir), '').strip(os.sep)
        return relative


class ProjectDirectory(Directory):
    def __init__(self, *bits):
        super(ProjectDirectory, self).__init__(*bits)

        self.template_dir = Directory(self.path, 'template')
        self.input_dir = Directory(self.path, 'input')

