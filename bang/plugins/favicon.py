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
from __future__ import unicode_literals, division, print_function, absolute_import
from collections import OrderedDict

from ..compat import *
from ..event import event
from ..path import Imagepath
from ..utils import Url


class Favicons(object):

    # safari requests apple-touch-icon.png and apple-touch-icon-precomposed.png
    # automatically
    regex = r"^(favicon\S*\.\S+|apple-touch-icon\S*.png)$"

    @property
    def outline(self):
        d = OrderedDict()

        # generic
        d["icon"] = [
            32,
            57,
            76,
            96,
            128,
            192,
            228,
            1024
        ]

        # android
        d["shortcut-icon"] = [
            196
        ]

        # iOS
        d["apple-touch-icon"] = [
            120,
            152,
            180,
        ]

        return d

    def __init__(self, input_dirs, *paths, **kwargs):
        self.images = []
        self.input_dirs = input_dirs

        regex = kwargs.get("regex", self.regex)
        for input_dir in self.input_dirs:
            for f in input_dir.files().regex(regex, filename=True):
                im = Imagepath(f)
                im.input_dir = input_dir
                self.images.append(im)

    def __str__(self):
        return self.__bytes__() if is_py2 else self.__unicode__()

    def __unicode__(self):
        return self.html()

    def __bytes__(self):
        return ByteString(self.unicode())

    def __bool__(self):
        return len(self.images) > 0
    __nonzero__ = __bool__

    def get_image_info(self):
        d = {}
        for im in self.images:
            if im.is_favicon():
                d["favicon"] = im
            else:
                d[im.width] = im

        return d

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
        image_d = self.get_image_info()
        outline_d = self.outline

        if "favicon" in image_d:
            ret.append(OrderedDict([
                ("rel", "icon"),
                ("href", Url(
                    "/",
                    image_d["favicon"].relative_to(image_d["favicon"].input_dir)
                )),
                ("type", "image/x-icon"),
                ("sizes", self.icon_sizes(image_d["favicon"])),
            ]))

        for rel, sizes in outline_d.items():
            for size in sizes:
                if size in image_d:
                    ret.append(OrderedDict([
                        ("rel", rel),
                        ("href", Url(
                            "/",
                            image_d[size].relative_to(image_d[size].input_dir)
                        )),
                        ("sizes", self.icon_sizes(image_d[size])),
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
def configure_favicon(event, config):
    config.favicons = Favicons(config.project.input_dirs)
    config.favicons_html = config.favicons.html()


@event("output.template")
def template_output_favicon(event, config):
    event.html = event.html.inject_into_head(config.favicons_html)

