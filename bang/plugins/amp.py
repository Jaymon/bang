# -*- coding: utf-8 -*-
"""
Google amp plugin

This creates amp/index.html files in each of the Page directories and adds an amp
url to the header of the regular pages

You can test amp validation in Chrome by appending #development=1 to an amp url
and opening a DevTools window on the Console tab

    https://amp.dev/documentation/guides-and-tutorials/start/converting/building-page/
    https://github.com/Jaymon/bang/issues/34
    https://amp.dev/documentation/guides-and-tutorials/start/converting/resolving-errors/?format=websites
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import logging
import re

from ..compat import *
from ..event import event, extend
from ..md.extensions import Extension, Treeprocessor, Postprocessor
from ..md.extensions.embed import (
    YoutubeProcessor as BaseYoutubeProcessor,
    TwitterProcessor as BaseTwitterProcessor,
    InstagramProcessor as BaseInstagramProcessor,
    VimeoProcessor as BaseImageProcessor,
)
from ..types import PageIterator, Page
from ..utils import Url
from ..path import File, Image
from ..config import Config, Theme


logger = logging.getLogger(__name__)


class AmpProcessor(object):
    def add_component(self):
        """
        https://amp.dev/documentation/guides-and-tutorials/start/add_advanced/adding_components/
        """
        self.md.config.amp_components.add(
            '<script async custom-element="{}" src="{}"></script>'.format(
                self.component_name,
                self.component_src
            )
        )


class YoutubeProcessor(BaseYoutubeProcessor, AmpProcessor):
    """
    https://amp.dev/documentation/components/amp-youtube/?format=websites
    """
    component_name = "amp-youtube"

    component_src = "https://cdn.ampproject.org/v0/amp-youtube-0.1.js"

    def get_embed_code(self, url):
        ytid = self.get_id(url)
        self.add_component()
        embed_html = [
            '<amp-youtube',
            'data-videoid="{}"'.format(ytid),
            'layout="responsive"',
            'width="{}" height="{}"></amp-youtube>'.format(560, 315),
        ]
        return " ".join(embed_html)


class TwitterProcessor(BaseTwitterProcessor, AmpProcessor):
    """
    https://amp.dev/documentation/components/amp-twitter/?format=websites
    """
    component_name = "amp-twitter"

    component_src = "https://cdn.ampproject.org/v0/amp-twitter-0.1.js"

    def get_html(self, url, body):
        self.add_component()
        tweetid = self.get_id(url)
        width = body["width"]
        height = body.get("height", None)
        if not height:
            height = width

        embed_html = [
            '<amp-twitter',
            'data-tweetid="{}"'.format(tweetid),
            'layout="responsive"',
            'width="{}" height="{}"></amp-youtube>'.format(width, height),
        ]

        return " ".join(embed_html)


class InstagramProcessor(BaseInstagramProcessor, AmpProcessor):
    """
    https://amp.dev/documentation/components/amp-instagram/
    """
    component_name = "amp-instagram"

    component_src = "https://cdn.ampproject.org/v0/amp-instagram-0.1.js"


    def get_html(self, url, body):
        self.add_component()
        igid = self.get_id(url)
        width = body["thumbnail_width"]
        height = body.get("thumbnail_height", width)

        embed_html = [
            '<amp-instagram',
            'data-shortcode="{}"'.format(igid),
            'data-captioned',
            'layout="responsive"',
            'width="{}" height="{}"></amp-youtube>'.format(width, height),
        ]

        return " ".join(embed_html)


class VimeoProcessor(BaseImageProcessor, AmpProcessor):
    """
    https://amp.dev/documentation/components/amp-vimeo/?format=websites
    """
    component_name = "amp-vimeo"

    component_src = "https://cdn.ampproject.org/v0/amp-vimeo-0.1.js"

    def get_embed_code(self, url):
        self.add_component()

        vid = self.get_id(url)
        width = 640
        height = 360

        embed_html = [
            '<amp-vimeo',
            'data-videoid="{}"'.format(vid),
            'layout="responsive"',
            'width="{}" height="{}"></amp-youtube>'.format(width, height),
        ]

        return " ".join(embed_html)


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


class IframePostprocessor(Postprocessor, AmpProcessor):
    """
    https://amp.dev/documentation/guides-and-tutorials/develop/media_iframes_3p/iframes/?format=websites
    """
    component_name = "amp-iframe"

    component_src = "https://cdn.ampproject.org/v0/amp-frame-0.1.js"

    IFRAME_REGEX = re.compile(r"<(/?)iframe(\s*)", re.I)

    def iframe_callback(self, m):
        return "<{}amp-iframe{}".format(m.group(1), m.group(2))

    def run(self, text):
        text, iframe_count = self.IFRAME_REGEX.subn(self.iframe_callback, text)
        if iframe_count > 0:
            self.add_component()
            logger.debug("Amp found {} iframes in text".format(iframe_count))

        return text


class AmpExtension(Extension):
    def extendMarkdown(self, md):
        md.register(self, AmpTreeprocessor(md), [">ImageTreeprocessor", ">AbsoluteLinkTreeprocessor"])
        md.register(self, IframePostprocessor(md), ["_end"])

        plugins = [
            YoutubeProcessor(md),
            TwitterProcessor(md),
            InstagramProcessor(md),
            VimeoProcessor(md),
        ]

        for instance in plugins:
            md.register(self, instance)


@event("configure.plugins")
def configure_plugins_amp(event, config):
    config.setdefault("amp_iter", PageIterator(config))


@event('context.amp')
def configure_context_amp(event, config):
    md = config.markdown
    md.register(AmpExtension())

    # amp will first check if current theme has amp support, if it doesn't then it
    # will fallback to the default theme
    theme = config.theme
    if not theme.template_dir.has_directory("amp"):
        config.theme_name = "default"
    config.template_prefix = "amp"

    # amp components (eg, Twitter, Youtube, and iframe) will set components into
    # this so they can be added to the head of the html file
    config.amp_components = set()


@extend.property(Page, "amp_url")
def amp_url(self):
    """returns the amp permalink url for this page"""
    return "{}/amp/".format(self.url.rstrip("/"))


@event("output.template.page")
def output_amp(event, config):
    # sanity check, we only want to run this callback if we aren't already
    # running it, otherwise we would infinitely recurse
    if config.is_context("amp"):
        return

    instance = event.instance

    with config.context("amp") as config:
        theme = config.theme

        instance.amp_output_file = instance.output_dir.child_file("amp", instance.output_basename)

        instance.output_dir.child_directory("amp").create()

        instance.output_template(
            instance.amp_output_file,
            theme=theme
        )


@event("output.template.page")
def template_amp(event, config):

    instance = event.instance

    if config.is_context("amp"):
        s = '<link rel="canonical" href="{}">'.format(instance.url)

        if config.amp_components:
            event.html = event.html.inject_into_head("\n".join(config.amp_components))

    else:
        s = '<link rel="amphtml" href="{}">'.format(instance.amp_url)

    event.html = event.html.inject_into_head(s)

