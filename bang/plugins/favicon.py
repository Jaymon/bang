# -*- coding: utf-8 -*-
"""
This plugin will find any favicon.* image in the root input/ directory and then
create the html for the head of an html page and then inject that html into a
rendered html template, basically, it generates something like this and adds it
to the <head> tag:

    <!-- generics -->
    <link rel="icon" href="/path/to/favicon-32.png" sizes="32x32">
    <link rel="icon" href="/path/to/favicon-57.png" sizes="57x57">
    <link rel="icon" href="/path/to/favicon-76.png" sizes="76x76">
    <link rel="icon" href="/path/to/favicon-96.png" sizes="96x96">
    <link rel="icon" href="/path/to/favicon-128.png" sizes="128x128">
    <link rel="icon" href="/path/to/favicon-192.png" sizes="192x192">
    <link rel="icon" href="/path/to/favicon-228.png" sizes="228x228">

    <!-- Android -->
    <link rel="shortcut icon" sizes="196x196" href=“/path/to/favicon-196.png">

    <!-- iOS -->
    <link rel="apple-touch-icon" href="/path/to/favicon-120.png" sizes="120x120">
    <link rel="apple-touch-icon" href="path/to/favicon-152.png" sizes="152x152">
    <link rel="apple-touch-icon" href="path/to/favicon-180.png" sizes="180x180">


These are the links I used to figure out what to support:
    https://www.emergeinteractive.com/insights/detail/the-essentials-of-favicons/
    https://github.com/audreyr/favicon-cheat-sheet
"""
import re
from collections import OrderedDict

from ..compat import *
from ..event import event
from ..path import Imagepath, Dirpath
from ..utils import Url


class Favicons(object):

    # safari requests apple-touch-icon.png and apple-touch-icon-precomposed.png
    # automatically
    regex = r"^(favicon\S+|apple-touch-icon\S+|android-chrome\S+)$"

    def __init__(self, **kwargs):
        self.images = []
        self.regex = kwargs.get("regex", self.regex)

    def __str__(self):
        return self.html()

    def __bytes__(self):
        return ByteString(self.__str__())

    def __bool__(self):
        return len(self.images) > 0

    def add_dir(self, path: Dirpath):
        for f in path.files().regex(self.regex, filename=True):
            im = Imagepath(f)
            im.base_dir = path
            self.images.append(im)

    def icon_sizes(self, imagepath):
        """produce sizes WxH for link sizes attribute

        https://www.w3schools.com/tags/att_sizes.asp
        """
        sizes = []
        info = imagepath.get_info()
        for width, height in info["dimensions"]:
            sizes.append("{}x{}".format(width, height))
        return " ".join(sizes)

    def get_info(self):
        ret = []

        for im in self.images:
            if im.is_favicon():
                ret.append(OrderedDict([
                    ("rel", "icon"),
                    ("href", Url(
                        "/",
                        im.relative_to(im.base_dir),
                    )),
                    ("type", "image/x-icon"),
                    ("sizes", self.icon_sizes(im)),
                ]))

            else:
                if "apple-touch-icon" in im.basename:
                    rel = "apple-touch-icon"

                elif "android-chrome" in im.basename:
                    rel = "shortcut-icon"

                else:
                    rel = ""

                    outline_d = {
                        "icon": [ # generic
                            32,
                            57,
                            76,
                            96,
                            128,
                            192,
                            228,
                            1024,
                        ],
                        "shortcut-icon": [ # android
                            196,
                        ],
                        "apple-touch-icon": [ # iOS
                            120,
                            152,
                            180,
                        ],
                    }

                    im_size = im.width
                    for size_rel, sizes in outline_d.items():
                        for size in sizes:
                            if size == im_size:
                                rel = size_rel
                                break

                        if rel:
                            break

                    if not rel:
                        rel = "icon"

                ret.append(OrderedDict([
                    ("rel", rel),
                    ("href", Url(
                        "/",
                        im.relative_to(im.base_dir),
                    )),
                    ("sizes", self.icon_sizes(im)),
                ]))

        return ret

    def html(self):
        ret = []
        info = self.get_info()
        for d in info:
            attrs = []
            for n, v in d.items():
                attrs.append('{}="{}"'.format(n, v))
            ret.append("<link {}>".format(" ".join(attrs)))

        return "\n".join(ret)


@event("configure.plugins")
def configure_favicon(event):
    config = event.config
    config.favicons = Favicons()

    for input_dir in config.project.input_dirs:
        config.favicons.add_dir(input_dir)


@event("output.template")
def template_output_favicon(event):
    config = event.config
    event.html = event.html.inject_into_head(config.favicons.html())


@event("compile.assets")
def configure_favicon_assets(event):
    """Hook into the `assets` plugin to allow favicons to be found in the
    assets directories also."""
    favicons = event.config.favicons

    if assets := event.config.assets:
        for basename, asset in assets.other.items():
            if re.match(favicons.regex, basename):
                im = Imagepath(asset.output_file)
                im.base_dir = event.config.project.output_dir
                favicons.images.append(im)

