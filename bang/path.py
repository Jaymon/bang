# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import sys
import re
from distutils import dir_util
import shutil
import codecs
import logging
import fnmatch
import struct
import imghdr
import hashlib

from datatypes import (
    Path,
    Dirpath as BaseDirpath,
    Filepath as BaseFilepath,
    Imagepath as BaseImagepath
)

from .compat import *
from .event import event


logger = logging.getLogger(__name__)


class PathMixin(object):
    def is_private(self):
        basename = self.basename
        return basename.startswith("_") or basename.startswith(".")

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
        """Alias for relative_to, all .relative() calls should be converted and this
        should be removed"""
        raise DeprecationWarning("Convert relative call to relative_to")
        return self.relative_to(ancestor_dir) if ancestor_dir else self.relative_to()

    def clone(self):
        """return a new instance with the same path"""
        d = type(self)(self.path)
        d.ancestor_dir = self.ancestor_dir
        return d

    def contents(self, encoding=""):
        raise DeprecationWarning("Convert contents call to read_text or read_bytes")
        return self.read_text(encoding=encoding)

    
    def create(self, contents, encoding=""):
        """create the file with basename in this directory with contents"""
        raise DeprecationWarning("Convert create to write_text or write_bytes")
        logger.debug("create file {}".format(self.path))
        self.write_text(contents, encoding=encoding)
        return self


class Filepath(BaseFilepath, PathMixin):
    pass


class Imagepath(BaseImagepath, PathMixin):
    def sizes(self):
        sizes = []
        info = self.get_info()
        for width, height in info["dimensions"]:
            sizes.append("{}x{}".format(width, height))
        return " ".join(sizes)


class Dirpath(BaseDirpath, PathMixin):
    def file_contents(self, *parts):
        """return the contents of the basename file in this directory"""
        raise DeprecationWarning("This should be tightend up to use file_text or file_bytes")
        return self.file_text(*parts)

    def has_index(self):
        """returns True if this directory has an index.* file already"""
        for f in self.files(r'^index\.'):
            return True
        return False


class DataDirpath(Dirpath):
    def __new__(cls, modpath=""):
        if not modpath:
            modpath = __name__.split(".")[0]
        base_dir = os.path.dirname(sys.modules[modpath].__file__)
        return super().__new__(cls, base_dir, "data")

#     def __init__(self, modpath=""):
#         if not modpath:
#             modpath = __name__.split(".")[0]
#         base_dir = os.path.dirname(sys.modules[modpath].__file__)
#         super().__init__(base_dir, "data")

    def themes_dir(self):
        return self.child_dir("themes")

    def project_dir(self):
        return self.child_dir("project")


