# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import imp
import hashlib
from contextlib import contextmanager
from collections import defaultdict
import importlib

from .event import event
from .types import Other, Aux, Post


class Bangfile(object):
    """load a Bangfile"""
    @classmethod
    def get_file(cls, directory, basename="bangfile.py"):
        """get the bangfile in the given directory with the given basename

        directory -- Directory|string -- usually the project_dir, the directory that
            contains the bangfile to be loaded
        basename -- string -- the basename of the bangfile
        """
        module = None
        config_file = os.path.join(str(directory), basename)
        if os.path.isfile(config_file):
            # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
            h = "bangfile_{}".format(hashlib.md5(config_file).hexdigest())
            module = imp.load_source(h, config_file)

        return module

    def get_module(cls, modpath):
        module = importlib.import_module(modpath)
        return module

    def __init__(self, dir_or_modpath, *args, **kwargs):
        if os.path.isdir(str(dir_or_modpath)):
            self.module = self.get_file(dir_or_modpath, *args, **kwargs)
        else:
            self.module = self.get_module(dir_or_modpath)


class Config(object):
    """A context aware configuration class, really this is a glorified getter/setter
    but you can change the context by setting .context_name which means you can
    change values and then when you switch contexts the values will reset to what
    they were, this is handy for having a little different configuration in your
    feed as opposed to your web

    How this works is config keeps a history of the context changes, so when you request
    a value it will check the current context, if there is no value there it will
    check for that value in the previous context, all the way down the line
    """

    _context_name = ""

    _previous_context_name = ""

    @property
    def context_name(self):
        return self._context_name

    @property
    def input_dir(self):
        return self.project.input_dir

    @property
    def output_dir(self):
        return self.project.output_dir

    @property
    def template_dir(self):
        return self.project.template_dir

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
        """return a dict of all active values in the config at the moment"""
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

    def __init__(self, project):
        #self._context_name_stack = [""]

        self.__dict__["_fields"] = defaultdict(dict)
        self._context_name = type(self)._context_name
        self._previous_context_name = type(self)._previous_context_name

        self.project = project

        self.dirtypes = [Aux, Post, Other]

        self.bangfiles = [
            Bangfile(project.project_dir),
            Bangfile("bang.bangfile")
        ]

        # TODO -- https://github.com/Jaymon/bang/issues/41 this should force
        # re-calling events that have fired
        #event.push("config", self.config)
        event.push("configure", self)

    @contextmanager
    def context(self, name, **kwargs):
        """This is meant to be used with the "with ..." command, its purpose is to
        make it easier to change the context and restore it back to the previous context
        when it is done

        :Example:
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
        return self.get(k)

    def __setattr__(self, k, v):
        if k in self.__dict__ or k in self.__class__.__dict__:
            super(Config, self).__setattr__(k, v)
        else:
            self.set(k, v)

    def load_environ(self, prefix="BANG_"):
        """find all environment vars and add them into this instance"""
        for k, v in os.environ.items():
            if k.startswith(prefix):
                self.set(k[5:].lower(), v)

