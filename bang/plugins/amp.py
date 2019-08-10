# -*- coding: utf-8 -*-
"""
Google amp plugin
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

#from markdown.treeprocessors import Treeprocessor

from ..compat import *
from ..event import event
from ..md.extensions import Extension, Treeprocessor
from ..types import PageIterator
from ..utils import Url
from ..path import File, Image


logger = logging.getLogger(__name__)


class AmpTreeprocessor(Treeprocessor):
    """Handles converting certain tags to their amp equivalent
    """
    def run(self, doc):
        config = self.md.config

        #pout.b("amp start")
        # https://amp.dev/documentation/guides-and-tutorials/develop/media_iframes_3p/?format=websites
        for elem in self.get_tags(doc, "img"):
            u = Url(elem.get("src"))

            elem.tag = "amp-img"
            if u and u.is_local(config):
                f = config.project.input_dir.child(u.path)
                im = Image(f)
                elem.set("width", String(im.width))
                elem.set("height", String(im.height))
                elem.set("layout", "responsive")

                # https://amp.dev/documentation/guides-and-tutorials/develop/media_iframes_3p/?format=websites#animated-images
                if im.is_animated():
                    elem.tag = "amp-anim"


        # https://amp.dev/documentation/guides-and-tutorials/develop/media_iframes_3p/?format=websites#video
        for elem in self.get_tags(doc, "video"):
            elem.tag = "amp-video"
            # TODO -- add width and height? Ugh


        # TODO -- support audio? It's a little more complex because it needs a
        # js script included in the head, we might just be able to put that js
        # script in the head for everything though
        # https://amp.dev/documentation/guides-and-tutorials/develop/media_iframes_3p/?format=websites#audio
        #pout.b("amp stop")


class AmpExtension(Extension):
    """"""
    def extendMarkdown(self, md):

        md.register(self, AmpTreeprocessor(md), [">image", ">AbsoluteLinkExtension"])




#         md.registerExtension(self)
# 
#         md.treeprocessors.register(
#             AmpTreeprocessor(md),
#             "amp",
#             self.find_priority(md.treeprocessors, ["image", "absolute_link"])
#         )

        #pout.v(md.treeprocessors)

        #self.processor = AmpTreeprocessor(md)
        #md.treeprocessors.add('amp', self.processor, "_end")











@event("configure.plugins")
def configure(event_name, config):
    config.setdefault("amp_iter", PageIterator(config))



@event('context.amp')
def configure(event_name, config):
    md = config.markdown
    md.register(AmpExtension())
    #md.registerExtensions(extensions=[AmpExtension()], configs={})








@event('output.finish')
def output_amp(event_name, config):
    with config.context("amp") as config:
        for p in config.amp_iter:
            pout.v(p.html)

