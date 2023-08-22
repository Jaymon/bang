# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

from .config import Config, Bangfile
from .event import event
from .path import Dirpath
from .event import event
from .decorators import once


__version__ = "2.3.0"


logger = logging.getLogger(__name__)


class Project(object):

    config_class = Config

    def __init__(self, project_dir, output_dir):
        self.project_dir = Dirpath(project_dir)
        self.output_dir = Dirpath(output_dir)
        #self.input_dir = self.project_dir.child_dir('input')
        self.input_dirs = [
            self.project_dir.child_dir('input'),
        ]
        self.config = self.config_class(self)
        self.types = {}

        self.configure()

    def is_private_basename(self, basename):
        """This is used by the project to decide if a basename of a file/folder is
        considered private and therefore shouldn't be traversed

        This is here in config so it could be overridden if needed
        """
        return basename.startswith("_") or basename.startswith(".")

    def __iter__(self):
        """Iterate through the files found in self.input_dir

        :returns: yields tuples of (relpath, input_file, output_dir) where
            relpath is the relative path of the file to self.input_dir, input_file
            is the full path to the file and output_dir is the full folder path
            (subdir of self.output_dir) where the file should be copied.
        """
        is_private_cb = self.config.get(
            "is_private_callback",
            self.is_private_basename
        )

        for input_dir in self.input_dirs:
            input_files = input_dir.files().not_callback(
                is_private_cb,
                basenames=True
            )
            for input_file in input_files:
                relpath = input_file.relative_to(input_dir)
                output_dir = self.output_dir.child_file(relpath).parent
                yield relpath, input_file, output_dir

    def get_types(self, type_name):
        """return the instances of type_name found during project compile"""
        types = self.types.get(type_name, None)
        if types is None:
            for type_class in self.config.types:
                if type_name == type_class.name:
                    types = type_class.instances_class(self.config)
                    self.types[type_name] = types

            if types is None:
                raise ValueError(f"No defined pages class for type [{type_name}]")

        return types

    def configure(self):
        event.bind_callback_params(config=self.config)

        event.push("configure.start")

        Bangfile("{}.bangfile".format(self.config.module_name))
        Bangfile(self.project_dir),

        event.push("configure.plugins")
        event.push("configure.project")

        theme = self.config.theme
        Bangfile(theme.theme_dir)

        # theme configuration comes after project configuration because project
        # configuration will most likely set the theme to be used
        theme.configure()
        event.push("configure.theme")
        event.push("configure.theme.{}".format(theme.name))

        # do any cleanup after finishing the configure phase, this should only
        # be called by user edited bangfiles so they can do any final overriding
        event.push("configure.finish")

        logger.debug(f"Project project_dir: {self.project_dir}")
        for i, input_dir in enumerate(self.input_dirs, 1):
            logger.debug(f"Project input_dir {i}: {input_dir}")
        logger.debug(f"Project output_dir: {self.output_dir}")
        logger.debug(f"Project theme: {theme.name} ({theme.theme_dir})")

    def compile(self):
        """go through project's input/ directory and find all the different types

        This just populates self.types but doesn't do any actual outputting and is
        really only broken out from output() for easier testing"""
        event.broadcast("compile.start")

        self.config.theme.compile()

        self.types = {}
        type_classes = self.config.types

        for relpath, input_file, output_dir in self:
            for type_class in type_classes:
                if type_class.match(input_file.basename):
                    types = self.get_types(type_class.name)
                    instance = type_class(input_file, output_dir, self.config)
                    logger.debug(f"Found: {instance}")
                    types.append(instance)
                    break

        # do any cleanup after finishing the compile phase
        event.broadcast("compile.finish")

    def output(self):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.compile()

        # conceptually the same event as compile.finish but here for completeness
        # and easier readability of the intention of a callback in a bangfiles
        event.broadcast('output.clear')

        if self.output_dir.exists():
            logger.info("Clearing output directory")
            self.output_dir.clear()

        event.broadcast('output.start')

        with self.config.context("output") as config:

            config.theme.output()

            for type_name, instances in self.types.items():

                event.broadcast(f'output.start.{type_name}')
                logger.debug(f"{type_name}: {len(instances)} instance(s)")

                for instance in instances:
                    instance.output()

                event.broadcast(f'output.finish.{type_name}')

        event.broadcast('output.finish')

