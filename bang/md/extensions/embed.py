# -*- coding: utf-8 -*-
import re
import tempfile
import json
import os
import logging

import xml.etree.ElementTree as etree
#import requests

from ...path import Dirpath
from . import Extension, Postprocessor, Blockprocessor as BaseBlockprocessor
from ...utils import HTML, HTTPClient


logger = logging.getLogger(__name__)


class LinkifyPostprocessor(Postprocessor):
    """This goes through and links any plain links in the body of the html

    other linkify example:
        https://github.com/Jaymon/Montage/blob/master/plugins/Utilities/src/Str.php
    """

    # http://daringfireball.net/2010/07/improved_regex_for_matching_urls
    LINKIFY_RE = re.compile(r'''\b
      (                              # Capture 1: entire matched URL
        (?:
          [a-z][\w-]+:               # URL protocol and colon
          (?:
            /{1,3}                   # 1-3 slashes
            |                        #   or
            [a-z0-9%]                # Single letter or digit or %
                                     # (Trying not to match e.g. "URI::Escape")
          )
          |                          #   or
          www\d{0,3}[.]              # "www.", "www1.", "www2." … "www999."
          |                          #   or
          [a-z0-9.\-]+[.][a-z]{2,4}/ # looks like domain name ending with slash
        )
        (?:                          # One or more:
          [^\s()<>]+                 # Run of non-space, non-()<>
          |                          #   or
          \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
        )+
        (?:                          # End with:
          \(([^\s()<>]+|(\([^\s()<>]+\)))*\) # balanced parens, up to 2 levels
          |                                  #   or
          [^\s`!()\[\]{};:\'".,<>?«»“”‘’]    # not one of these chars
        )
      )''', re.I | re.X)

    def run(self, text):
        def subn_callback(m):
            return '<a class="embed" href="{}">{}</a>'.format(
                m.group(0),
                m.group(0)
            )

        text_linked = ""
        s = HTML(text)
        for tag, plain in s.blocks(ignore_tagnames=["a", "pre"]):
            plain_linked, made = self.LINKIFY_RE.subn(
                subn_callback, # r'<a class="embed" href="\0">\0</a>',
                plain
            )
            text_linked += tag
            text_linked += plain_linked

        return text_linked


class Blockprocessor(BaseBlockprocessor):
    """
    https://github.com/waylan/Python-Markdown/blob/master/markdown/blockparser.py
    """
    def get_id(self, url):
        m = self.id_regex.search(url)
        return m.group(1) if m else None

    def test(self, parent, block):
        return self.test_regex.match(block.strip()) and self.get_id(block)

    def get_figure(self, parent, name):
        if self.parser.md.output_format in ["html"]:
            figure = etree.SubElement(parent, 'figure')
            figure.set("class", "embed {}".format(name))

        else:
            figure = etree.SubElement(parent, 'div')
            figure.set("class", "embed figure {}".format(name))

        return figure


class YoutubeProcessor(Blockprocessor):
    """This will convert a plain youtube link to an embedded youtube video

    fun fact, this is based on some super old php code I wrote for noopsi.com
    in the mid 2000s
    """
    test_regex = re.compile(r"^https?:\/\/(?:www\.)?youtube\.", re.I)

    id_regex = re.compile(r"v=([^&]*)")

    def get_embed_code(self, url):
        ytid = self.get_id(url)
        vid_url = f"https://www.youtube.com/embed/{ytid}"
        attrs = (
            'width="{}"'
            ' height="{}"'
            ' frameborder="0"'
            ' allowfullscreen'
        ).format(560, 315)
        embed_html = f'<iframe {attrs} src="{vid_url}"></iframe>'
        return embed_html

    def run(self, parent, blocks):
        block = blocks.pop(0)
        embed_html = self.get_embed_code(block)
        if embed_html:
            figure = self.get_figure(parent, "youtube")
            placeholder = self.parser.md.htmlStash.store(embed_html)
            figure.text = placeholder


class TwitterProcessor(Blockprocessor):
    """
    https://dev.twitter.com/rest/reference/get/statuses/oembed
    https://dev.twitter.com/web/embedded-tweets
    """
    filename = "twitter.json"

    base_url = "https://publish.twitter.com/oembed"

    test_regex = re.compile(
        r"^https?:\/\/(?:[^\.]+\.)?twitter\.[^\/]+\/.+$",
        flags=re.I
    )

    id_regex = re.compile(r"/(\d+)/?$")

    name = "twitter"

    def get_cache_directory(self):
        cache_dir = self.md.page.input_dir.child_dir("_embed")
        return Dirpath(cache_dir)

    def read_cache(self):
        cache = {}
        d = self.get_cache_directory()
        contents = d.file_bytes(self.filename)
        if contents:
            cache = json.loads(contents)
        return cache

    def write_cache(self, cache):
        d = self.get_cache_directory()
        contents = json.dumps(cache)
        d.add_file(self.filename, contents)

    def get_html(self, url, body):
        return body["html"]

    def get_embed_code(self, url):
        cache = self.read_cache()

        # first we check cache, if it isn't in cache then we query twitter
        if url in cache:
            body = cache[url]
            html = self.get_html(url, body)

        else:
            html, body = self.get_response(url)
            cache[url] = body
            self.write_cache(cache)

        return html

    def get_response(self, url, **params):
        html = ""
        body = {}

        params["url"] = url
        res = HTTPClient().get(self.base_url, params)

        if res.status_code >= 200 and res.status_code < 400:
            body = res.json()
            html = self.get_html(url, body)

        else:
            logger.error("Embed for {} failed with code {}".format(
                url,
                res.status_code
            ))

        return html, body

    def run(self, parent, blocks):
        url = blocks.pop(0).strip()
        html = self.get_embed_code(url)

        # if we have the contents then we can load them up
        if html:
            figure = self.get_figure(parent, self.name)
            placeholder = self.parser.md.htmlStash.store(html)
            figure.text = placeholder


class VimeoProcessor(Blockprocessor):
    """This will convert a plain vimeo link to an embedded vimeo video

    fun fact, this is based on some super old php code I wrote for noopsi.com
    in the mid 2000s
    """
    test_regex = re.compile(r"^https?:\/\/([a-z0-9._-]+\.)?vimeo\.", re.I)

    id_regex = re.compile(r"\.com/(\d+)/?$")

    def get_embed_code(self, url):
        vid = self.get_id(url)
        vid_url = f"https://player.vimeo.com/video/{vid}"
        attrs = [
            'class="vimeo-media"',
            'width="{}"'.format(640),
            'height="{}"'.format(360),
            'frameborder="0"',
            'webkitallowfullscreen',
            'mozallowfullscreen',
            'allowfullscreen',
        ]

        embed_html = "\n".join([
            '<iframe src="vid_url" {}>'.format(" ".join(attrs)),
            '</iframe>'
        ])

        return embed_html

    def run(self, parent, blocks):
        block = blocks.pop(0).strip()
        embed_html = self.get_embed_code(block)
        if embed_html:
            figure = self.get_figure(parent, "vimeo")
            placeholder = self.parser.md.htmlStash.store(embed_html)
            figure.text = placeholder


class EmbedImageProcessor(Blockprocessor):
    """This will take a plain link to an image and convert it into an
    <img> tag

    it only works on links that end with an image extension like .jpg
    """
    test_regex = re.compile(
        r"^(?:[^\s\]\[\:<>]+|https?\:\/\/\S+?)"
        r"\.(?:jpe?g|gif|bmp|png|ico|tiff)$",
        re.I
    )

    def get_id(self, url):
        return True

    def run(self, parent, blocks):
        block = blocks.pop(0).strip()
        figure = self.get_figure(parent, "image")
        figure.text = '![{}]({} "")'.format(os.path.basename(block), block)


class EmbedExtension(Extension):
    """This will embed youtube, twitter, or raw links.

    to embed a Youtube or tweet you should put the link on its own line:

        text before

        https://twitter.com/foo/status/100

        text after

    Any link that isn't already wrapped in an <a> tag will be wrapped in an
    <a> tag automatically
    """
    def extendMarkdown(self, md):
        md.register(self, LinkifyPostprocessor(md))

        plugins = [
            YoutubeProcessor(md),
            TwitterProcessor(md),
            VimeoProcessor(md),
            EmbedImageProcessor(md),
        ]

        for instance in plugins:
            md.register(self, instance, "<paragraph")

