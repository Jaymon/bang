# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
#from collections import defaultdict
import logging

from .config import Config, Bangfile
from .event import event
from .server import Server
from .path import Directory
from .event import event
from .skeleton import Skeleton
from .decorators import once


__version__ = "0.2.12"


logger = logging.getLogger(__name__)


class Project(object):

    config_class = Config

    def __init__(self, project_dir, output_dir):
        self.project_dir = Directory(project_dir)
        self.output_dir = Directory(output_dir)
        self.template_dir = Directory(self.project_dir, 'template')
        self.input_dir = Directory(self.project_dir, 'input')
        self.config = self.config_class(self)
        self.types = {}

        self.configure()

    def configure(self):
        Bangfile("{}.bangfile".format(self.config.module_name))
        Bangfile(self.project_dir),

        event.push("configure.plugins", self.config)
        event.push("configure.project", self.config)
        event.push("configure", self.config) # deprecated 8-5-2019, move to configure.project

        theme = self.config.theme
        Bangfile(theme.theme_dir)

        event.push("theme", self.config)
        event.push("theme.{}".format(theme.name), self.config)

    def __iter__(self):
        return self.input_dir.copy_paths(self.output_dir)

    def get_type(self, type_name):
        """return the instances of type_name found during project compile"""
        return self.types.get(type_name, [])

    def compile(self):
        """go through project's input/ directory and find all the different types

        This just populates self.types but doesn't do any actual outputting and is
        really broken out from output() for easier testing"""

        self.types = {}

        for input_dir, output_dir in self:
            for dt_class in self.config.types:
                if dt_class.match(input_dir):
                    if dt_class.name not in self.types:
                        instances = dt_class.pages_class(self.config)
                        self.types[dt_class.name] = instances
                    else:
                        instances = self.types[dt_class.name]

                    logger.debug("{}: /{}".format(dt_class.name, input_dir.relative()))
                    instance = dt_class(input_dir, output_dir, self.config)
                    instances.append(instance)
                    break


    def output(self, regex=None):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.compile()

        with self.config.context("html") as config:

            if regex:
                logger.warning("output directory {} not cleared because regex present".format(self.output_dir))
                logger.warning("output.start event not broadcast because regex present")
            else:
                logger.info("Clearing output directory")
                self.output_dir.clear()

                event.broadcast('output.start', config)
                config.theme.output()

            for name, instances in self.types.items():
                logger.debug("{}: {} pages".format(name, len(instances)))
                for instance in instances.filter(regex):
                    instance.output()

        if regex:
            logger.warning("output.finish event not broadcast because regex present")
        else:
            event.broadcast('output.finish', config)

