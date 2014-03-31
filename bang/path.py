import os
import re
from distutils import dir_util
import shutil
import types
import codecs

from . import echo

class Directory(object):

    #content_file_regex = ur'\.(md|html|txt|markdown)$'
    content_file_regex = ur'\.(md|html|markdown)$'

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

    def create_file(self, basename, contents):
        """create the file with basename in this directory with contents"""
        output_file = os.path.join(self.path, basename)
        echo.out("create file {}", output_file)

        oldmask = os.umask(0)
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
        echo.out("copy file {} to {}", input_file, output_file)
        return shutil.copy(input_file, output_file)

    def create(self):
        """create the directory path"""
        echo.out("create dir: {}", self.path)
        return dir_util.mkpath(self.path)

    def clear(self):
        """this will clear a directory path of all files and folders"""
        # http://stackoverflow.com/a/1073382/5006
        echo.out("clearing {}", self.path)
        dir_util.mkpath(self.path)
        for root, dirs, files in os.walk(self.path, topdown=True):
            for td in dirs:
                shutil.rmtree(os.path.join(root, td))

            for tf in files:
                os.unlink(os.path.join(root, tf))

            break

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
            dirs.sort()
            for basename in dirs:
                d = Directory(root_dir, basename)
                d.ancestor_dir = self
                if not d.is_private():
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

