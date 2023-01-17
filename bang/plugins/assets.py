# -*- coding: utf-8 -*-
"""
Checks Assets.DIRNAME directory in project directory and theme directory and moves them
to an output directory assets/ directory with versioned (md5 hash) filenames. It
will automatically inject the javascript and css links into head
"""
from __future__ import unicode_literals, division, print_function, absolute_import
from collections import OrderedDict, defaultdict
import itertools
import re

from ..event import event
from ..path import Filepath, Dirpath
from ..utils import Url
from ..decorators import once


class Asset(object):
    """Primarily handles versioning of CSS and JS files"""
    def __init__(self, input_file, output_dir, config, **properties):
        self.input_file = input_file
        self.output_file = ""
        self.url = ""
        self.output_dir = output_dir
        self.config = config
        self.properties = properties

    def compile(self):
        """The compile phase, go through all the assets and figure out what their
        output path will be"""
        if self.is_url():
            self.output_file = self.input_file

        else:
            basename = self.input_file.basename
            checksum = self.input_file.checksum()
            self.output_file = Filepath(self.output_dir, "{}.{}".format(checksum, basename))

    def output(self):
        """output phase, go through all the assets and actually copy them over to
        the output directory"""
        if self.is_url():
            self.url = self.output_file

        else:
            self.input_file.copy_to(self.output_file)

            relative = self.output_file.relative(self.output_dir.ancestor_dir)
            relative = relative.replace('\\', '/')
            self.url = Url("{}/{}".format(self.config.base_url, relative))

    def is_url(self):
        """True if input_file was a url"""
        return isinstance(self.input_file, Url)

    def html(self):
        """Generate url for the asset"""
        return self.url

    def properties_html(self):
        """Generate the properties for an HTML tag"""
        props = []
        for name, val in self.properties.items():
            props.append('{}="{}"'.format(name, val))
        return " " + " ".join(props) if props else ""


class CSS(Asset):
    """Hanldes CSS specific assets"""
    def html(self):
        return '<link rel="stylesheet" href="{}" type="text/css"{}>'.format(
            self.url,
            self.properties_html(),
        )


class JS(Asset):
    """Hanldes javascript specific assets"""
    def html(self):
        return '<script src="{}"{}></script>'.format(
            self.url,
            self.properties_html(),
        )


class Assets(object):
    """An instance of this class will be available at config.assets.

    Assets are stored by basename -> path, so, if you had <INPUT-DIR>/assets/app.css
    then you could grab it by doing `config.assets.get("app.css")`
    """
    DIRNAME = "assets"
    """this is the directory that is checked for input and the name of the output
    directory also"""

    css_class = CSS
    js_class = JS
    asset_class = Asset

    def __init__(self, output_dir, config):
        self.css = {}
        self.js = {}
        self.other = {}
        self._order = {}
        self._header_html = ""
        self._body_html = ""
        #self.lookup = defaultdict(dict)

        self.output_dir = Dirpath(output_dir, self.DIRNAME)
        self.output_dir.ancestor_dir = output_dir

        self.config = config

    def add_dir(self, path):
        """Add a directory to check for a DIRNAME directory inside path

        :param path: str, this directory path will be checked for a .DIRNAME directory
        inside of it
        """
        assets_dir = Dirpath(path, self.DIRNAME)
        if assets_dir.exists():
            for path in assets_dir.files(depth=0):
                self.add(path)

    def add(self, path, **properties):
        """This will add an asset at path and when the html is generated it will
        have those properties

        :param path: str, a local path or URL for the asset
        :param **properties: dict, key/val of html tag properties
        """
        ext = ""
        asset_class = self.asset_class
        if Url.match(path):
            f = Url(path)
            basename = f.basename
            ext = f.ext
            d = getattr(self, f.ext, self.other)

        else:
            f = Filepath(path)
            basename = f.basename
            ext = f.ext

        d = getattr(self, f.ext, self.other)
        if ext == "css":
            asset_class = self.css_class
        elif ext == "js":
            asset_class = self.js_class

        d[basename] = asset_class(f, self.output_dir, self.config, **properties)

    def add_script(self, s, body=False):
        """add a script body

        NOTE -- currently you can only have one script, so if this is called twice
        then the second call will overwrite the first, I got it working for my needs
        right now with the idea I would come in and make it more robust later (5-10-2022)

        :param s: str, this will be wrapped by <script></script>
        :param body: bool, True if you want this script injected right before </body>
        """
        if body:
            self._body_html = s
        else:
            raise ValueError("Operation not currently supported")

    def get(self, name):
        """Get an asset

        :param name: str, the name of the asset you want
        """
        for d in [self.css, self.js, self.other]:
            if name in d:
                return d[name]
        raise NameError(name)

    def __iter__(self):
        for a in itertools.chain(self.css.items(), self.js.items(), self.other.items()):
            yield a

    def compile(self):
        """The compile phase"""
        for name, asset in self:
            asset.compile()

    def output(self):
        """the output phase"""
        for name, asset in self:
            asset.output()

    def head_html(self):
        """This generates the head html that will be injected right before </head>

        :returns: str, the html to inject into the head
        """
        if not self._header_html:
            for name, asset in itertools.chain(self.css.items(), self.js.items()):
                found = False
                for k in ["before", "order", "after"]:
                    order = self._order[k]
                    for regex in order:
                        for i in range(len(order)):
                            regex = order[i]
                            if not isinstance(regex, (self.css_class, self.js_class)):
                                if re.search(regex, name):
                                    found = True
                                    order[i] = asset

                        if found:
                            break

                    if found:
                        break

                if not found:
                    self._order["order"].append(asset)

            html = []
            for k in ["before", "order", "after"]:
                for row in self._order[k]:
                    if isinstance(row, (self.css_class, self.js_class)):
                        html.append(row.html())
            self._header_html = "\n".join(html)
        return self._header_html

    def body_html(self):
        """this generates the body javascript that will be injected right before </body>

        :returns: str, the script tag to inject into the body
        """
        return "\n".join([
            '<script type="application/javascript">',
            self._body_html,
            '</script>',
        ])

    def order(self, order=None, before=None, after=None):
        """Handles ordering of the .head_html() output

        This is kind of strange, and in a perfect world wouldn't be needed, but basically
        this will place any assets that match regexes in before first, then put all
        the regexes in order in the middle and then all the after regexes last, in the
        order those regexes are in each of their lists.

        Let's say we had an asset directory like this:

            <THEME-DIR>/assets/
                bar.css
                baz.css
                che.css
                foo.css

        and we want them to be in this order: foo.css, baz.css, che.css, bar.css,
        then we could do:

            config.assets.order(before=[r"foo", r"baz"], after=["bar"])

        :param order: list, a list of regexes, the middle order you want the assets to be in
        :param before: list, a list of regexes, these will come before order
        :param after: list, a list of regexes, these will come after order
        """

        self._order = {
            "order": order or [],
            "before": before or [],
            "after": after or [],
        }


@event('configure.theme')
def configure_assets(_, config):
    assets = Assets(config.project.output_dir, config)
    assets.add_dir(config.project.project_dir)
    assets.add_dir(config.theme.theme_dir)
    config.assets = assets

    event.broadcast("configure.assets", config)


@event('compile.finish')
def compile_assets(event, config):
    config.assets.compile()


@event('output.html.start')
def context_html(event, config):
    config.assets.output()


@event("output.template")
def template_output_favicon(event, config):
    event.html = event.html.inject_into_head(config.assets.head_html())
    event.html = event.html.inject_into_body(config.assets.body_html())

