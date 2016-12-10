# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import imp
import hashlib
from contextlib import contextmanager

from . import event


configs = {}

context_name = "global"


def initialize(project_dir):
    """init the configuration, really only needs to be called once per run"""
    Bangfile.load(project_dir)


def get(name=""):
    """Get the configuration at name, if no name is specified then return the Config
    instance found at the global context_name, whenever a new context is created it
    will broadcast a "context.name" event with the Config instance, this will allow
    a bangfile to customize the specific configuration for that context"""
    global configs
    global context_name

    # if we didn't pass in a name then we use the current context_name
    if not name:
        name = context_name

    if name not in configs:
        configs[name] = Config()
        configs[name].context_name = name
        event.broadcast("context.{}".format(name), configs[name])

    return configs[name]


@contextmanager
def context(name, **kwargs):
    """This is meant to be used with the "with ..." command, its purpose is to
    make it easier to change the context and restore it back to the previous context
    when it is done

    example --
        with config.context("foo"):
            # anything in this block will use the foo configuration
            pass
        # anything outside this block will not use the foo configuration
    """
    global context_name
    previous_context_name = context_name
    context_name = name

    config = get(name)

    # passed in values get set on the instance directly
    for k, v in kwargs.items():
        setattr(config, k, v)

    yield config

    context_name = previous_context_name


class ContextAware(object):
    """parent class for any object that wants to be able to pull context aware
    configuration instances easily and automatically"""
    @property
    def config(self):
        """Returns the configuration of the current Context instance"""
        return get()


class Bangfile(object):
    """The purpose of this class is to call Bangfile.load(project_dir) once and 
    forever have access to the loaded bangfile
    """

    module = None
    """Will hold the loaded bangfile singleton"""

    @classmethod
    def get(cls, directory, basename="bangfile.py"):
        """get the bangfile in the given directory with the given basename

        directory -- Directory|string -- usually the project_dir, the directory that
            contains the bangfile to be loaded
        basename -- string -- the basename of the bangfile
        """
        module = None
        config_file = os.path.join(str(directory), basename)
        if os.path.isfile(config_file):
            # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
            h = hashlib.md5(config_file).hexdigest()
            module = imp.load_source(h, config_file)

        return module

    @classmethod
    def load(cls, *args, **kwargs):
        """same as get but this will actually set the module into the module class
        variable, this way it becomes a singleton
        """
        cls.module = cls.get(*args, **kwargs)


class Config(object):
    """small wrapper around the config module that takes care of what happens if
    the config file doesn't actually exist"""
    @property
    def base_url(self):
        """Return the base url with scheme (scheme) and host and everything, if scheme
        is unknown this will use // (instead of http://) but that might make things
        like the rss feed and sitemap fail if they are used so it is recommended you
        set the scheme in your bangfile, there is a similar problem if host is empty, then
        it will just return empty string"""
        base_url = ''
        scheme = self.scheme
        if scheme:
            base_url = '{}://{}'.format(scheme, self.host)

        else:
            host = self.host
            if host:
                base_url = '//{}'.format(host)

        return base_url

    def __init__(self):
        self.environ = {}

        # find all environment vars
        for k, v in os.environ.items():
            if k.startswith('BANG_'):
                name = k[5:].lower()
                self.environ[name] = v

    def get(self, k, default_val=None):
        """bangfile takes precedence, then environment variables"""
        ret = default_val
        module = Bangfile.module
        if module:
            ret = getattr(module, k, self.environ.get(k, default_val))

        else:
            ret = self.environ.get(k, default_val)

        return ret

    def __getattr__(self, k):
        return self.get(k)


