# -*- coding: utf-8 -*-
"""
Checks Assets.DIRNAME directory in project directory and theme directory and
moves them to <PROJECT-OUTPUT-DIR>/assets/ with versioned (md5 hash) filenames.
It will also automatically inject the javascript and css links into head
"""
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
            self.output_file = Filepath(
                self.output_dir,
                "{}.{}".format(checksum, basename)
            )

    def output(self):
        """output phase, go through all the assets and actually copy them over to
        the output directory"""
        if self.is_url():
            self.url = self.output_file

        else:
            self.input_file.copy_to(self.output_file)

            relative = self.output_file.relative_to(self.config.output_dir)
            relative = relative.replace('\\', '/')
            self.url = Url("{}/{}".format(self.config.base_url, relative))

    def is_url(self):
        """True if input_file was a url"""
        return isinstance(self.input_file, Url)

    def is_private(self):
        """Is this asset considered private?"""
        basename = self.input_file.basename
        return self.config.project.is_private_basename(basename)

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
    """Handles CSS specific assets"""
    def html(self):
        return '<link rel="stylesheet" href="{}" type="text/css"{}>'.format(
            self.url,
            self.properties_html(),
        )


class JS(Asset):
    """Handles javascript specific assets"""
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
    css_class = CSS
    js_class = JS
    asset_class = Asset

    @property
    def dirname(self):
        """this is the directory that is checked for input and the name of the output
        directory also"""
        return self.config.get("assets_dir", "assets")

    def __init__(self, output_dir, config):
        self.css = {}
        self.js = {}
        self.other = {}
        self._header_html = ""
        self._body_html = ""

        self.config = config
        self.order()

        self.output_dir = config.output_dir.child_dir(self.dirname)

    def add_dir(self, path):
        """Add a directory to check for a DIRNAME directory inside path

        :param path: str, this directory path will be checked for a .DIRNAME directory
        inside of it
        """
        assets_dir = Dirpath(path, self.dirname)
        if assets_dir.exists():
            for path in assets_dir.files(depth=0):
                self.add(path)

    def add(self, path, ext="", **properties):
        """This will add an asset at path and when the html is generated it will
        have those properties

        :param path: str, a local path or URL for the asset
        :param **properties: dict, key/val of html tag properties
        """
        asset_class = self.asset_class
        if Url.is_url(path):
            f = Url(path)
            basename = f.basename
            ext = ext or f.ext 

        else:
            f = Filepath(path)
            basename = f.basename
            ext = ext or f.ext

        if not self.config.project.is_private_basename(basename):
            d = getattr(self, ext, self.other)
            if ext == "css":
                asset_class = self.css_class

            elif ext == "js":
                asset_class = self.js_class

            d[basename] = asset_class(
                f,
                self.output_dir,
                self.config,
                **properties
            )

    def add_script(self, s, body=False):
        """add a script body

        NOTE -- currently you can only have one script, so if this is called
        twice then the second call will overwrite the first, I got it working
        for my needs right now with the idea I would come in and make it more
        robust later (5-10-2022)

        :param s: str, this will be wrapped by <script></script>
        :param body: bool, True if you want this script injected right before
            </body>
        """
        if body:
            self._body_html = s

        else:
            raise ValueError("Operation not currently supported")

    def get(self, basename):
        """Get an asset

        :param basename: str, the name of the asset you want
        """
        for d in [self.css, self.js, self.other]:
            if basename in d:
                return d[basename]

        raise NameError(basename)

    def ordered(self, css=True, js=True, other=True):
        """This will order the CSS and JS and yield the Asset instances in the
        order specified in the last .order() call

        :param css: bool, True if you want to order CSS assets
        :param js: bool, True if you want to order JS assets
        :param other: bool, True if you want to order other assets
        """
        ret = OrderedDict()
        ret["before"] = OrderedDict()
        ret["order"] = OrderedDict()
        ret["order"][""] = []
        ret["after"] = OrderedDict()

        chained = []
        if css:
            chained.append(self.css.items())

        if js:
            chained.append(self.js.items())

        if other:
            chained.append(self.other.items())

        #it = itertools.chain(self.css.items(), self.js.items())
        it = itertools.chain(*chained)

        for name, a in it:
            found = False
            for k in ret:
                regexes = self._order[k]
                for regex in regexes:
                    ret[k].setdefault(regex, [])
                    if re.search(regex, name):
                        ret[k][regex].append(a)
                        found = True
                        break

                if found:
                    break

            if not found:
                ret["order"][""].append(a)

        for k in ret:
            for regex in ret[k]:
                for a in ret[k][regex]:
                    yield a

    def __iter__(self):
        it = itertools.chain(
            self.css.values(),
            self.js.values(),
            self.other.values()
        )

        for a in it:
            yield a

    def compile(self):
        """The compile phase"""
        for asset in self:
            asset.compile()

    def output(self):
        """the output phase"""
        for asset in self:
            asset.output()

    def css_inline(self):
        """Generates all the css as a body that can go between a <style></style>
        html tag. This is basically the raw css

        :returns: str, the CSS code that is suitable to be placed in the body
            of a <style> tag
        """
        ret = []
        for a in self.ordered(css=True, js=False, other=False):
            if not isinstance(a.input_file, Url):
                ret.append(a.input_file.read_text())

        return "\n".join(ret)

    def html_links(self):
        """This generates the head html that will be injected right before
        </head>

        :returns: str, the html to inject into the head
        """
        ret = []
        for a in self.ordered(css=True, js=True, other=False):
            ret.append(a.html())

        return "\n".join(ret)

    def html_body(self):
        """this generates the body javascript that will be injected right before
        </body>

        :returns: str, the script tag to inject into the body
        """
        return "\n".join([
            '<script type="application/javascript">',
            self._body_html,
            '</script>',
        ])

    def order(self, order=None, before=None, after=None):
        """Handles ordering of the .head_html() output

        This is kind of strange, and in a perfect world wouldn't be needed, but
        basically this will place any assets that match regexes in before first,
        then put all the regexes in order in the middle and then all the after
        regexes last, in the order those regexes are in each of their lists.

        Let's say we had an asset directory like this:

            <THEME-DIR>/assets/
                bar.css
                baz.css
                che.css
                foo.css

        and we want them to be in this order: foo.css, baz.css, che.css, bar.css,
        then we could do:

            config.assets.order(before=[r"foo", r"baz"], after=["bar"])

        :param order: list, a list of regexes, the middle order you want the
            assets to be in
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
    assets.add_dir(config.theme.theme_dir)
    assets.add_dir(config.project.project_dir)
    config.assets = assets

    event.broadcast("configure.assets")


@event('compile.finish')
def compile_assets(event, config):
    config.assets.compile()


@event('output.start')
def context_html(event, config):
    config.assets.output()


@event("output.template")
def template_output_favicon(event, config):
    if config.is_context("amp"):
        event.html = event.html.inject_into_head("\n".join([
            "<style amp-custom>",
            config.assets.css_inline(),
            "</style>",
        ]))

    else:
        event.html = event.html.inject_into_head(config.assets.html_links())
        event.html = event.html.inject_into_body(config.assets.html_body())

