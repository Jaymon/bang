import os
import codecs
from distutils import dir_util
import datetime
import imp
import re
import logging

from .event import event
from .config import ContextAware, Bangfile, Config
from .path import Directory, Project
from .types import Other, Aux, Post, Directories


logger = logging.getLogger(__name__)


class Site(ContextAware):
    """this is where all the magic happens. Output generates all the posts and compiles
    files from input directory to output directory"""
    @property
    def project_dir(self):
        return self.config.project.project_dir

    @property
    def output_dir(self):
        return self.config.project.output_dir

    @property
    def template_dir(self):
        return self.config.project.template_dir

    def __init__(self, project_dir, output_dir):
        self.config = Config()
        self.config.project = Project(project_dir, output_dir)

    # !!! Not sure which name I like better
    def analyze(self): return self.compile()
    def compile(self):
        """go through input/ dir and compile the files"""
        self.config.dirtypes = [Aux, Post, Other]
        self.config.bangfile = Bangfile(self.project_dir)
        event.push("config", self.config)

        # this isn't efficient but we go in and create placeholders for all the dirtypes
        for dt_class in self.config.dirtypes:
            instances = dt_class.list_class(self)
            setattr(self, dt_class.list_name, instances)

        with self.config.context("web") as conf:
            for input_dir, output_dir in conf.project:
                for dt_class in conf.dirtypes:
                    if dt_class.match(input_dir):
                        logger.debug("{}: {}".format(dt_class.__name__, input_dir.relative()))
                        instance = dt_class(input_dir, output_dir, self)
                        instances = getattr(self, instance.list_name)
                        instances.append(instance)
                        break

    def output(self, regex=None):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.compile()

        with self.config.context("web") as conf:
            if regex:
                logger.warning("output directory {} not cleared because regex present".format(self.output_dir))
            else:
                logger.info("Clearing output directory")
                self.output_dir.clear()

            for dt_class in conf.dirtypes:
                instances = getattr(self, dt_class.list_name, None)
                if instances:
                    for instance in instances.matching(regex):
                        instance.output()

                if regex:
                    logger.warning("Posts not compiled because regex present")
                else:
                    if dt_class is Post:
                        # this compiles the root index.html
                        if instances:
                            output_cb = getattr(instances, "output")
                            if output_cb:
                                output_cb()

#                 for f in self.project_dir.input_dir.files():
#                     self.output_dir.copy_file(f)

            if regex:
                logger.warning("output.finish event not broadcast because regex present")
            else:
                event.broadcast('output.finish', self)

