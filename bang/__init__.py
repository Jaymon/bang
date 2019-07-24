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
        self.pages = {}

        #self.configure()

    def configure(self):
        Bangfile(self.project_dir),
        Bangfile("{}.bangfile".format(self.config.module_name))
        #event.push("project", self.config)

    def __iter__(self):
        return self.input_dir.copy_paths(self.output_dir)
#         for subdirs in self.input_dir.copy_paths(self.output_dir):
#             yield subdirs

#         input_dir = self.input_dir.clone()
#         input_dir.ancestor_dir = self.input_dir
#         output_dir = self.output_dir.clone()
#         yield input_dir, output_dir
# 
#         for input_dir in self.input_dir:
#             output_dir = self.output_dir / input_dir.relative()
#             yield input_dir, output_dir

    def output(self, regex=None):
        """go through input/ dir and compile the files and move them to output/ dir"""
        self.configure()
        self.config.theme.configure()

        with self.config.context("global") as config:
            with self.config.context("web") as config:

                # go through input/ dir and compile the different types
                for input_dir, output_dir in self:
                    for dt_class in config.dirtypes:
                        if dt_class.match(input_dir):
                            if dt_class.name not in self.pages:
                                instances = dt_class.pages_class(self.config)
                                self.pages[dt_class.name] = instances
                            else:
                                instances = self.pages[dt_class.name]

                            logger.debug("{}: /{}".format(dt_class.name, input_dir.relative()))
                            instance = dt_class(input_dir, output_dir, config)
                            instances.append(instance)
                            break

                if regex:
                    logger.warning("output directory {} not cleared because regex present".format(self.output_dir))
                    logger.warning("output.start event not broadcast because regex present")
                else:
                    logger.info("Clearing output directory")
                    self.output_dir.clear()

                    event.broadcast('output.start', config)
                    config.theme.output()

                for name, instances in self.pages.items():
                    logger.debug("{}: {} pages".format(name, len(instances)))
                    for instance in instances.matching(regex):
                        instance.output()

            if regex:
                logger.warning("output.finish event not broadcast because regex present")
            else:
                event.broadcast('output.finish', config)

