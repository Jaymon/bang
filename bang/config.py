# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import imp
from contextlib import contextmanager
from collections import defaultdict
import importlib
import logging

from .compat import *
from .event import event
from .types import Other, Page
from .path import DataDirectory, Directory, TemplateDirectory
from .md import Markdown


logger = logging.getLogger(__name__)


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
        config_file = os.path.join(String(directory), basename)
        if os.path.isfile(config_file):
            # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
            h = "bangfile_{}".format(ByteString(config_file).md5())
            logger.debug("Running bangfile from file path {}".format(config_file))
            module = imp.load_source(h, config_file)

        return module

    def get_module(cls, modpath):
        logger.debug("Running bangfile with module path {}".format(modpath))
        module = importlib.import_module(modpath)
        return module

    def __init__(self, dir_or_modpath, *args, **kwargs):
        if os.path.isdir(String(dir_or_modpath)):
            self.module = self.get_file(dir_or_modpath, *args, **kwargs)
        else:
            self.module = self.get_module(dir_or_modpath)


class Config(object):
    """A context aware configuration class, really this is a glorified getter/setter
    but you can change the context using with .context(name) which means you can
    change values and then when you switch contexts the values will reset to what
    they were, this is handy for having a little different configuration in your
    feed as opposed to your web

    How this works is config keeps a history of the context changes, so when you request
    a value it will check the current context, if there is no value there it will
    check for that value in the previous context, all the way down the line
    """
    @property
    def default_theme_name(self):
        """the default theme name, .theme_name can change but this should stay
        constant since it is the fallback theme"""
        return "default"

    @property
    def default_theme(self):
        return self.themes[self.default_theme_name]

    @property
    def theme(self):
        return self.themes[self.theme_name]

    @property
    def module_name(self):
        """Returns the main module name of this package"""
        return __name__.split(".")[0]

    @property
    def input_dir(self):
        return self.project.input_dir

    @property
    def output_dir(self):
        return self.project.output_dir

    @property
    def context_name(self):
        return self._context_names[-1]

    @property
    def fields(self):
        """return a dict of all active values in the config at the moment"""
        fields = {}
        for context_name in self._context_names:
            fields.update(self._fields[context_name])
        return fields

    @property
    def markdown(self):
        context_name = self.context_name
        md = self._markdown_instances.get(context_name, None)
        if not md:
            logger.debug("Creating Markdown instance for context [{}]".format(context_name))
            extensions = self.get("markdown_extensions", None)
            md = Markdown.create_instance(self, extensions=extensions)
            self._markdown_instances[context_name] = md
        return md

    @property
    def page_types(self):
        """returns types of Page and above (any children of Page)"""
        return [t for t in self.types if issubclass(t, Page)]

    @property
    def base_url(self):
        """Return the base url with scheme (scheme) and host and everything, if scheme
        is unknown this will use // (instead of http://). If host is empty, then
        it will just return empty string regardless of the scheme setting"""
        base_url = ""
        scheme = self.scheme
        host = self.host

        if host:
            if scheme:
                base_url = '{}://{}'.format(scheme, host)

            else:
                base_url = '//{}'.format(host)

        return base_url

    def __init__(self, project):
        # we set support properties directly on the __dict__ so __setattr__ doesn't
        # infinite loop, context properties can just be set normally

        # a stack of the context names, where -1 is always the current active context
        self.__dict__["_context_names"] = [""]

        # this is where all the magic happens, the keys are the context names
        # and the values are the set properties for that context, 
        self.__dict__["_fields"] = defaultdict(dict)

        # holds a markdown instance for each context
        self.__dict__["_markdown_instances"] = dict()

        # initial settings for the themes
        self.__dict__["themes"] = {}
        self.add_themes(DataDirectory().themes_directory())
        project_themes_d = project.project_dir.child("themes")
        if project_themes_d.exists():
            self.add_themes(project_themes_d)
        self.theme_name = self.default_theme_name

        self.encoding = "UTF-8"
        self.lang = "en"

        self.project = project

        # order matters here, it should go from most strict matching to least
        self.types = [Page, Other]


        # TODO -- https://github.com/Jaymon/bang/issues/41 this should force
        # re-calling events that have fired
        #event.push("config", self.config)
        #event.push("configure", self) # deprecate this in favor of "project"?
        #event.push("config", self)

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
        self._context_names.append(name)

        # passed in values get set on the instance directly
        for k, v in kwargs.items():
            self.set(k, v)

        event.broadcast("context.{}".format(self.context_name), self)

        yield self

        event.broadcast("context.{}.finish".format(self.context_name), self)
        self._context_names.pop(-1)

    def add_themes(self, themes_dir):
        """a themes directory is a directory that contains themes, each theme in
        its own subdirectory (which is the name of the theme) so this will create
        Theme instances for all the immediate subdirectories of the passed in 
        themes_dir

        :param themes_dir: Directory, a directory where themes can be found
        """
        themes_dir = Directory(themes_dir)
        for theme_dir in themes_dir.directories():
            t = Theme(theme_dir, self)
            self.themes[t.name] = t

    def set(self, k, v):
        self._fields[self.context_name][k] = v

    def get(self, k, default_val=None):
        for context_name in reversed(self._context_names):
            fields = self._fields[context_name]
            if k in fields:
                return fields[k]

        return default_val

    def __getattr__(self, k):
        return self.get(k)

    def __setattr__(self, k, v):
        if k in self.__dict__ or k in self.__class__.__dict__:
            super(Config, self).__setattr__(k, v)
        else:
            self.set(k, v)

    def __setitem__(self, k, v):
        return self.__setattr__(k, v)

    def __getitem__(self, k):
        return self.__getattr__(k)

    def __contains__(self, k):
        for context_name in reversed(self._context_names):
            if k in self._fields[context_name]:
                return True
        return False

    def setdefault(self, k, v):
        if k not in self:
            self.set(k, v)

    def load_environ(self, prefix="BANG_"):
        """find all environment vars and add them into this instance"""
        for k, v in os.environ.items():
            if k.startswith(prefix):
                self.set(k[5:].lower(), v)

    def is_context(self, context_name):
        return self.context_name == context_name


class Theme(object):
    def __init__(self, theme_dir, config, **kwargs):
        self.theme_dir = theme_dir
        self.name = self.theme_dir.basename
        self.config = config
        self.template_dir = TemplateDirectory(
            self.theme_dir.child(kwargs.get("template_dir", "template"))
        )
        self.input_dir = self.theme_dir.child("input")

    def output(self):
        if self.input_dir.exists():
            logger.info("output theme [{}] input/ directory to {}".format(
                self.name,
                self.config.output_dir
            ))
            self.input_dir.copy_to(self.config.output_dir)

    def render_template(self, template_name, filepath, **kwargs):
        return self.template_dir.render(
            template_name,
            filepath,
            self.config,
            **kwargs
        )

    def output_template(self, template_name, filepath, **kwargs):
        return self.template_dir.output(
            template_name,
            filepath,
            self.config,
            **kwargs
        )

    def has_template(self, template_name):
        """Return True if the theme contains template_name"""
        return self.template_dir.has(template_name)

