# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import sys
#import logging

from datatypes import (
    Path,
    Dirpath,
    Filepath,
    Imagepath
)

from .compat import *
#from .event import event


#logger = logging.getLogger(__name__)


class DataDirpath(Dirpath):
    """Wrapper class to make working with the module's data directory easier to
    work with

    * https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package/58941536#58941536
    * https://setuptools.pypa.io/en/latest/userguide/datafiles.html
    * https://stackoverflow.com/questions/779495/access-data-in-package-subdirectory
    """
    def __new__(cls, modpath=""):
        if not modpath:
            modpath = __name__.split(".")[0]
        base_dir = os.path.dirname(sys.modules[modpath].__file__)
        return super().__new__(cls, base_dir, "data")

    def themes_dir(self):
        return self.child_dir("themes")

    def project_dir(self):
        return self.child_dir("project")


