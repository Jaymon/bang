import os
import codecs
from distutils import dir_util
import datetime
import imp
import re
import logging

from .event import event
from .config import ContextAware, Bangfile
from .path import Directory, DocumentDirectory, Project
from .utils import HTMLStripper, Template
from .types import Other, Aux, Post, Directories


logger = logging.getLogger(__name__)



class Site(ContextAware):
    """this is where all the magic happens. Output generates all the posts and compiles
    files from input directory to output directory"""
    @property
    def project_dir(self):
        return self.config.project_dir

    @property
    def output_dir(self):
        return self.config.output_dir

    @property
    def template_dir(self):
        return self.project_dir.template_dir

    def __init__(self, project_dir, output_dir):
        conf = self.config
        conf.project_dir = project_dir
        conf.output_dir = output_dir
        conf.project = Project(project_dir, output_dir)
        self.tmpl = Template(self.template_dir)

    def compile(self):
        """go through input/ dir and compile the files"""
        conf = self.config
        conf.bangfile = Bangfile(self.project_dir)
        conf.register_dirtype("auxs", Aux)
        conf.register_dirtype("posts", Post)
        conf.register_dirtype("others", Other)

        # this isn't efficient but we go in and create placeholders for all the diretypes
        for name, dt_class in conf.dirtypes:
            instances = getattr(self, name, None)
            if not instances:
                instances = dt_class.list_class(self)
                setattr(self, name, instances)

        with self.context("web") as conf:
            for d, output_dir in conf.project:
                for name, dt_class in conf.dirtypes:
                    if dt_class.match(d):
                        logger.debug("{}: {}".format(dt_class.__name__, d))
                        instance = dt_class(d, self)
                        instances.append(instance)
                        break

    def output(self, regex=None):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.compile()

        with self.context("web") as conf:
            if regex:
                logger.warning("output directory {} not cleared because regex present".format(conf.output_dir))
            else:
                conf.output_dir.clear()

            for name, dt_class in conf.dirtypes:
                instances = getattr(self, name, None)
                if instances:
                    for instance in instances:
                        instance.output(site=self)

                if regex:
                    logger.warning("Posts not compiled because regex present")
                else:
                    if dt_class is Post:
                        # this compiles the root index.html
                        if instances:
                            output_cb = getattr(instances, "output")
                            if output_cb:
                                output_cb(site=self)

#                 for f in self.project_dir.input_dir.files():
#                     self.output_dir.copy_file(f)

            if regex:
                logger.warning("output.finish event not broadcast because regex present")
            else:
                event.broadcast('output.finish', self)

