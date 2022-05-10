# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

from .config import Config, Bangfile
from .event import event
from .server import Server
from .path import Directory
from .event import event
from .decorators import once


__version__ = "1.1.0"


logger = logging.getLogger(__name__)


class Project(object):

    config_class = Config

    def __init__(self, project_dir, output_dir):
        self.project_dir = Directory(project_dir)
        self.output_dir = Directory(output_dir)
        self.input_dir = Directory(self.project_dir, 'input')
        self.config = self.config_class(self)
        self.types = {}

        self.configure()

    def configure(self):
        event.push("configure.start", self.config)

        Bangfile("{}.bangfile".format(self.config.module_name))
        Bangfile(self.project_dir),

        event.push("configure.plugins", self.config)
        event.push("configure.project", self.config)

        theme = self.config.theme
        Bangfile(theme.theme_dir)

        # theme configuration comes after project configuration because project
        # configuration will most likely set the theme to be used
        event.push("configure.theme", self.config)
        event.push("configure.theme.{}".format(theme.name), self.config)

        # do any cleanup after finishing the configure phase, this should only
        # be called by user edited bangfiles so they can do any final overriding
        event.push("configure.finish", self.config)

    def __iter__(self):
        return self.input_dir.copy_paths(self.output_dir)

    def get_type(self, type_name):
        """return the instances of type_name found during project compile"""
        ret = self.types.get(type_name, None)
        if ret is None:
            for dt_class in self.config.types:
                if type_name == dt_class.name:
                    ret = dt_class.pages_class(self.config)
                    self.types[type_name] = ret

            if ret is None:
                raise ValueError("No defined pages class for type [{}]".format(type_name))

        return ret

    def compile(self):
        """go through project's input/ directory and find all the different types

        This just populates self.types but doesn't do any actual outputting and is
        really only broken out from output() for easier testing"""
        event.broadcast("compile.start", self.config)

        self.types = {}

        for input_dir, output_dir in self:
            for dt_class in self.config.types:
                if dt_class.match(input_dir):
                    instances = self.get_type(dt_class.name)
                    logger.debug("{}: /{}".format(dt_class.name, input_dir.relative()))
                    instance = dt_class(input_dir, output_dir, self.config)
                    instances.append(instance)
                    break

        # do any cleanup after finishing the compile phase
        event.broadcast("compile.finish", self.config)

    def output(self, regex=None):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.compile()

        # conceptually the same event as compile.stop but here for completeness
        # and easier readability of the intention of a callback in a bangfiles
        event.broadcast('output.start', self.config)

        with self.config.context("html") as config:
            if regex:
                logger.warning("output directory {} not cleared because regex present".format(self.output_dir))
            else:
                logger.info("Clearing output directory")
                self.output_dir.clear()

                config.theme.output()

            event.broadcast('output.html.start', config)

            for name, instances in self.types.items():
                logger.debug("{}: {}".format(name, len(instances)))
                for instance in instances.filter(regex):
                    instance.output()

            event.broadcast('output.html.finish', config)

        if regex:
            logger.warning("output.finish event not broadcast because regex present")
        else:
            event.broadcast('output.finish', self.config)

