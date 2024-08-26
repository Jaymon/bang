# -*- coding: utf-8 -*-
import os
from contextlib import contextmanager
import logging

from jinja2 import Environment, FileSystemLoader
from datatypes import (
    OrderedSubclasses,
    Url,
    ContextNamespace,
    ReflectPath,
    ReflectModule,
)

from .compat import *
from .event import event
from .types import Page, Type, Other
from .path import (
    Path,
    DataDirpath,
    Dirpath,
    Filepath
)
from .md import Markdown
from .utils import HTML



logger = logging.getLogger(__name__)


class Bangfile(object):
    """load a Bangfile"""
    def get_dir(self, dirpath, basename="bangfile.py"):
        """get the bangfile in the given directory with the given basename

        directory -- Directory|string -- usually the project_dir, the directory
            that contains the bangfile to be loaded
        basename -- string -- the basename of the bangfile
        """
        return self.get_file(Filepath(dirpath, basename))

    def get_file(self, filepath):
        if filepath.isfile():
            # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
            h = "bangfile_{}".format(String(filepath).md5())
            logger.debug(f"Running bangfile with file path: {filepath}")
            return ReflectPath(filepath).exec_module(h)

    def get_module(self, modpath):
        logger.debug("Running bangfile with module path: {}".format(modpath))
        return ReflectModule(modpath).get_module()

    def __init__(self, path, **kwargs):
        """
        :param path: Path|str, This can be a file, directory, or module path
            file: /path/bangfile.py
            dir: /path/
            modulepath: foo.bar.bangfile
        """
        if Path.is_file_path(path):
            self.module = self.get_file(Filepath(path))

        elif Path.is_dir_path(path):
            self.module = self.get_dir(Dirpath(path))

        else:
            self.module = self.get_module(path)


class Config(ContextNamespace):
    """A context aware configuration class, really this is a glorified
    getter/setter but you can change the context using with .context(name)
    which means you can change values and then when you switch contexts the
    values will reset to what they were, this is handy for having a little
    different configuration in your feed as opposed to your web

    How this works is config keeps a history of the context changes, so when
    you request a value it will check the current context, if there is no value
    there it will check for that value in the previous context, all the way
    down the line
    """
    @property
    def theme(self):
        return self.themes[self.theme_name]

    @property
    def module_name(self):
        """Returns the main module name of this package"""
        return __name__.split(".")[0]

    @property
    def output_dir(self):
        return self.project.output_dir

    @property
    def fields(self):
        """return a dict of all active values in the config at the moment"""
        return self.copy()

    @property
    def markdown(self):
        """Returns a unique markdown instance for each context"""
        context = self.current_context()
        md = context.get("_markdown_instance", None)
        if not md:
            logger.debug("Creating Markdown instance for context [{}]".format(
                self.context_name()
            ))
            extensions = self.get("markdown_extensions", None)
            md = Markdown.create_instance(self, extensions=extensions)
            context["_markdown_instance"] = md
        return md

    @property
    def base_url(self):
        """Return the base url with scheme (scheme) and host and everything, if
        scheme is unknown this will use // (instead of http://). If host is
        empty, then it will just return empty string regardless of the scheme
        setting"""
        if self.host:
            return Url(scheme=self.scheme, hostname=self.host)

        else:
            return Url()

    @property
    def page_types(self):
        """returns types of Page and above (any children of Page)"""
        return [t for t in self.types if issubclass(t, Page)]

    @property
    def types(self):
        return Type.classes

    def __init__(self, project):
        super().__init__("global")

        # we set support properties directly on the __dict__ so __setattr__
        # doesn't infinite loop, context properties can just be set normally

        # initial settings for the themes
        self.theme_name = "default"
        self.add_themes(DataDirpath().themes_dir())
        project_themes_dir = project.project_dir.child_dir("themes")
        if project_themes_dir.exists():
            self.add_themes(project_themes_dir)

        self.encoding = "UTF-8"
        self.lang = "en"
        self.page_output_basename = "index.html"

        self.project = project

    @contextmanager
    def context(self, name, **kwargs):
        """This is meant to be used with the "with ..." command, its purpose is
        to make it easier to change the context and restore it back to the
        previous context when it is done

        :Example:
            with config.context("foo"):
                # anything in this block will use the foo configuration
                pass
            # anything outside this block will *NOT* use the foo configuration
        """
        with super().context(name, **kwargs):
            # we use .once() here because if this context is used again we will
            # just pull the values from the already configured instance, so no
            # reason to go though and set everything again
            event.once(f"context.{self.context_name()}")

            yield self

            # we do not want to do a context.*.finish event because contexts
            # could be called multiple times in a run and so if something used
            # a finish event it could end up doing the same work over and over

    def add_themes(self, themes_dir):
        """a themes directory is a directory that contains themes, each theme
        in its own subdirectory (which is the name of the theme) so this will
        create Theme instances for all the immediate subdirectories of the
        passed in themes_dir

        :param themes_dir: Directory, a directory where themes can be found
        """
        # we always add the themes to the global context
        context = self.get_context(self._context_names[0])
        context.setdefault("themes", self.context_class())

        themes_dir = Dirpath(themes_dir)
        for theme_dir in themes_dir.dirs().depth(1):
            t = Theme(theme_dir, self)
            self.themes[t.name] = t

    def set(self, k, v):
        self[k] = v

    def __missing__(self, k):
        return None

    def load_environ(self, prefix="BANG_"):
        """find all environment vars and add them into this instance"""
        for k, v in os.environ.items():
            if k.startswith(prefix):
                self.set(k[len(prefix):].lower(), v)


class Theme(object):
    """Holds information about a theme

    Template functionality is a thin wrapper around Jinja functionality that
    handles templating things

    A theme directory is structured like this:

        <THEME NAME>/
            input/
            template/
                *.html

    The directory's basename will become .name. The input directory is
    processed just like any other input directories and used to populate the
    output directory. Any .html files in the template directory are what is
    used to template the markdown files. A page.md file would be templated with
    the page.html file, etc.

    The template_name would be the .html file's fileroot. So if you had a
    "page.html" template file, then the template_name would be "page"

    http://jinja.pocoo.org/docs/dev/
    https://jinja.palletsprojects.com/en/master/api/
    https://jinja.palletsprojects.com/en/2.10.x/

    template documentation:
        https://jinja.palletsprojects.com/en/2.10.x/templates/
    """
    @property
    def template(self):
        # https://jinja.palletsprojects.com/en/latest/api/#jinja2.Environment
        return Environment(
            loader=FileSystemLoader(self.template_dirs),
            #extensions=['jinja2.ext.with_'] # http://jinja.pocoo.org/docs/dev/templates/#with-statement
            lstrip_blocks=True,
            trim_blocks=True,
        )

    def __init__(self, theme_dir, config, **kwargs):
        self.theme_dir = theme_dir
        self.name = self.theme_dir.basename
        self.config = config
        self.input_dir = self.theme_dir.child_dir("input")
        self.template_dirs = [self.theme_dir.child_dir("template")]

    def get_template_name(self, template_name):
        parts = []
        prefix = self.config.get("template_prefix", "").strip("/")
        if prefix:
            parts.append(prefix)
        parts.append(template_name.strip("/"))
        return "/".join(parts)

    def get_template_info(self, template_name):
        template_name = self.get_template_name(template_name)
        return (template_name, f"{template_name}.html")

    def configure(self):
        """Called during project.configure but before configure.theme events"""
        if self.input_dir.exists():
            self.config.project.input_dirs.append(self.input_dir)

    def compile(self):
        """Called during project.compile"""
        pass

    def output(self):
        """Called during project.output"""
        pass

    def render_template(self, template_name, **kwargs):
        """
        https://jinja.palletsprojects.com/en/master/api/#jinja2.Template.render
        """
        template_name, template_relpath = self.get_template_info(template_name)
        tmpl = self.template.get_template(template_relpath)
        html = tmpl.render(config=self.config, **kwargs)

        logger.debug(f"Rendering HTML with template: {template_name}")

        r = event.broadcast(
            'output.template',
            html=HTML(html),
            template_name=template_name,
        )
        return r.html

    def output_template(self, template_name, filepath, **kwargs):
        """output kwargs using the template template_name to filepath

        :param template_name: string, the template you want to use for kwargs
        :param filepath: string, the destination file that will be output to
        :param **kwargs: dict, all these will be passed to the template
        """
        html = self.render_template(template_name, **kwargs)
        f = Filepath(filepath, encoding=self.config.encoding)
        f.write_text(html)

        logger.debug(f"Rendered HTML written to: {f}")

    def has_templates(self, dirname):
        """Return True if there is a directory in any of the template
        directories with dirname

        :param dirname: str, the directory that must be in one of the template
            directories. Directories are used to bundle specific templates
            together
        :returns: bool
        """
        for template_dir in self.template_dirs:
            if template_dir.has_dir(dirname):
                return True
        return False

    def has_template(self, template_name):
        """Return True if the theme contains template_name"""
        template_name, template_relpath = self.get_template_info(template_name)
        for template_dir in self.template_dirs:
            if template_dir.has_file(template_relpath):
                return True
        return False
        #return self.template_dir.has_file(template_relpath)

