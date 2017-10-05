# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import imp
import hashlib
from contextlib import contextmanager
from collections import defaultdict

from . import event


class ContextAware(object):
    """parent class for any object that wants to be able to pull context aware
    configuration instances easily and automatically"""
    @property
    def config(self):
        """Returns the configuration of the current Context instance"""
        global config
        return config


class Bangfile(object):
    """The purpose of this class is to call Bangfile.load(project_dir) once and 
    forever have access to the loaded bangfile
    """
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

    def __init__(self, directory, config, *args, **kwargs):
        self.module = self.get(directory, *args, **kwargs)
        event.broadcast("config", config)

#     @classmethod
#     def load(cls, *args, **kwargs):
#         """same as get but this will actually set the module into the module class
#         variable, this way it becomes a singleton
#         """
#         cls.module = cls.get(*args, **kwargs)


class Config(object):
    """small wrapper around the config module that takes care of what happens if
    the config file doesn't actually exist"""
#     instance = None

    _context_name = ""

    _previous_context_name = ""

    @property
    def context_name(self):
        return self._context_name

    @context_name.setter
    def context_name(self, v):
        self._previous_context_name = self._context_name
        self._context_name = v
        event.broadcast("context.{}".format(v), self)

    @context_name.deleter
    def context_name(self):
        self._context_name = self._previous_context_name
        self._previous_context_name = type(self)._previous_context_name

    @property
    def context_fields(self):
        """Return the fields set with the current context"""
        return self._fields[self.context_name]

    @property
    def global_fields(self):
        """return the fields set globally (no context fields)"""
        return self._fields[type(self)._context_name]

    @property
    def fields(self):
        fields = dict(self.global_fields)
        fields.update(self.context_fields)
        return fields

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

#     @classmethod
#     def create_instance(cls):
#         cls.instance = cls()
#         return cls.instance

    def __init__(self):
        self.__dict__["_fields"] = defaultdict(dict)

    @contextmanager
    def context(self, name, **kwargs):
        """This is meant to be used with the "with ..." command, its purpose is to
        make it easier to change the context and restore it back to the previous context
        when it is done

        example --
            with config.context("foo"):
                # anything in this block will use the foo configuration
                pass
            # anything outside this block will not use the foo configuration
        """
        self.context_name = name

        # passed in values get set on the instance directly
        for k, v in kwargs.items():
            self.set(k, v)

        yield self

        del self.context_name

    def set(self, k, v):
        self._fields[self.context_name][k] = v

    def get(self, k, default_val=None):
        """bangfile takes precedence, then environment variables"""
        ret = default_val
        fields = self.context_fields
        if k in fields:
            ret = fields[k]
        else:
            fields = self.global_fields
            if k in fields:
                ret = fields[k]

        return ret

    def __getattr__(self, k):
        #return super(Config, self).__getattr__(k)
        return self.get(k)
        #return self.fields[self.context_name][k]

    def __setattr__(self, k, v):
        if k in self.__dict__ or k in self.__class__.__dict__:
            super(Config, self).__setattr__(k, v)
        else:
            self.set(k, v)


def initialize(project_dir):
    """init the configuration, really only needs to be called once per run"""

    #self.environ = {}

    # find all environment vars
#     for k, v in os.environ.items():
#         if k.startswith('BANG_'):
#             name = k[5:].lower()
#             self.environ[name] = v

#     @event.bind("normalize.md", "normalize.markdown")
#     def markdown_to_html(self, document):


#     Bangfile.load(project_dir)


# the global configuration handler
config = Config()

# find all environment vars
for k, v in os.environ.items():
    if k.startswith('BANG_'):
        config.set(k[5:].lower(), v)

