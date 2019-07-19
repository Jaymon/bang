# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

from .config import Config
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

    def __iter__(self):
        input_dir = self.input_dir.clone()
        input_dir.ancestor_dir = self.input_dir
        output_dir = self.output_dir.clone()
        yield input_dir, output_dir

        for input_dir in self.input_dir:
            output_dir = self.output_dir / input_dir.relative()
            yield input_dir, output_dir

    def compile(self):
        """go through input/ dir and compile the different types"""
        #event.push("config", self.config)
        #event.push("configure", self.config)

        # create placeholders for all the dirtypes, we do this so any templates
        # won't have to check if the properties exist and can just start iterating
        for dt_class in self.config.dirtypes:
            instances = dt_class.list_class(self.config)
            setattr(self, dt_class.list_name, instances)

        with self.config.context("web") as conf:
            for input_dir, output_dir in conf.project:
                for dt_class in conf.dirtypes:
                    if dt_class.match(input_dir):
                        logger.debug("{}: {}".format(dt_class.__name__, input_dir.relative()))
                        instance = dt_class(input_dir, output_dir, self.config)
                        instances = getattr(self, instance.list_name)
                        instances.append(instance)
                        break

    def output(self, regex=None):
        """go through input/ dir and compile the files and move them to output/ dir"""
        with self.config.context("global") as conf:
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


                # TODO -- I was using threading.Thread instead of
                # multiprocess.Thread, I should try multiprocess threads since they
                # aren't bound by the GIL
                # this was NOT faster than syncronous, I could try green threads
    #             import threading
    #             from Queue import Queue
    #             import multiprocessing
    # 
    #             q = Queue()
    #             thread_count = multiprocessing.cpu_count()
    # 
    #             def target():
    #                 while True:
    #                     instance = q.get()
    #                     instance.output()
    #                     q.task_done()
    # 
    #             for i in range(thread_count):
    #                 t = threading.Thread(target=target)
    #                 t.daemon = True
    #                 t.start()
    # 
    #             for dt_class in conf.dirtypes:
    #                 instances = getattr(self, dt_class.list_name, None)
    #                 if instances:
    #                     for instance in instances.matching(regex):
    #                         q.put(instance)

                if regex:
                    logger.warning("output.finish event not broadcast because regex present")
                else:
                    event.broadcast('output.finish', self.config)

