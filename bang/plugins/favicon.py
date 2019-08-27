# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
from collections import OrderedDict

from ..event import event
from ..path import File, Directory, Image
from ..utils import Url


class Favicons(object):

    regex = r"^favicon\S*\.\S+$"

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

    def __init__(self, input_dir, *paths, **kwargs):
        self.images = []
        self.input_dir = input_dir

        regex = kwargs.get("regex", self.regex)
        for f in input_dir.files(regex=regex):
            self.images.append(Image(f))

#         for p in paths:
#             if isinstance(p, Image):
#                 self.images.append(p)
# 
#             elif isinstance(p, File):
#                 self.images.append(Image(p))
# 
#             elif isinstance(p, Directory):
#                 regex = kwargs.get("regex", r"^favicon\.\S+$")
#                 for f in p.files(regex=regex):
#                     self.images.append(Image(f))
# 
#             else:
#                 raise ValueError("Favicons only takes Image, File, or Directory instances")

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

    def get_info(self):

        ret = []
        image_d = self.get_image_info()
        outline_d = self.outline

        if "favicon" in image_d:
            ret.append(OrderedDict([
                ("rel", "icon"),
                ("href", Url("/", image_d["favicon"].relative(self.input_dir))),
                ("type", "image/x-icon"),
                ("sizes", image_d["favicon"].sizes()),
            ]))

        for rel, sizes in outline_d.items():
            for size in sizes:
                if size in image_d:
                    ret.append(OrderedDict([
                        ("rel", rel),
                        ("href", Url("/", image_d[size].relative(self.input_dir))),
                        ("sizes", image_d[size].sizes()),
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
    config.favicons = Favicons(config.project.input_dir)
    config.favicons_html = config.favicons.html()


@event("output.template")
def template_output_favicon(event, config):
    event.html = event.html.inject_into_head(config.favicons_html)

