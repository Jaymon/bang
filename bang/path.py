import os
import re
from distutils import dir_util
import shutil

class Directory(object):

    @property
    def basename(self):
        return os.path.basename(self.path)

    def __init__(self, *bits):
        self.path = ''
        if bits:
            bits = list(bits)
            bits[0] = self.normalize(bits[0])
            self.path = os.path.join(*bits)

    @classmethod
    def normalize(cls, d):
        """completely normalize a relative path (a path with ../, ./, or ~/)"""
        return os.path.abspath(os.path.expanduser(d))

    def clear(self):
        """this will clear a directory path of all files and folders"""
        # http://stackoverflow.com/a/1073382/5006
        dir_util.mkpath(self.path)
        for root, dirs, files in os.walk(self.path, topdown=True):
            for td in dirs:
                shutil.rmtree(os.path.join(root, td))

            for tf in files:
                os.unlink(os.path.join(root, tf))

            break

        return True

    def __str__(self):
        return self.path

    def __unicode__(self):
        return u"" + self.path

    def __iter__(self):
        for root_dir, dirs, _ in os.walk(self.path, topdown=True):
            dirs.sort()
            for basename in dirs:
                yield Directory(root_dir, basename)

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

    def is_post(self):
        """return true if this directory has a blog post in it"""
        return not self.is_aux() and self.files('\.(md|html|txt)$')

    def is_aux(self):
        """return True if this is a directory with an index.* file in it"""
        ret_bool = False
        if self.files('^index\.'):
            ret_bool = True

        return ret_bool

    def is_private(self):
        basename = self.basename
        return basename.startswith('_')


class ProjectDirectory(Directory):
    def __init__(self, *bits):
        super(ProjectDirectory, self).__init__(*bits)

        self.template_dir = Directory(self.path, 'template')
        self.input_dir = Directory(self.path, 'input')

