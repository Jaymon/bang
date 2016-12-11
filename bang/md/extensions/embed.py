# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re
import tempfile
import json
import os
import logging

from markdown import util
from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor
from markdown.blockprocessors import BlockProcessor as BaseBlockProcessor
import requests

from ...path import Directory


logger = logging.getLogger(__name__)


class Scanner(object):
    """Python implementation of Obj-c Scanner

    https://github.com/Jaymon/PlusPlus/blob/master/PlusPlus/NSString%2BPlus.m
    """
    def __init__(self, text):
        self.text = text
        self.offset = 0
        self.length = len(self.text)

    def to(self, char):
        """scans and returns string up to char"""
        partial = ""
        while (self.offset < self.length) and (self.text[self.offset] != char):
            partial += self.text[self.offset]
            self.offset += 1

        return partial

    def until(self, char):
        """similar to to() but includes the char"""
        partial = self.to(char)
        if self.offset < self.length:
            partial += self.text[self.offset]
            self.offset += 1
        return partial

    def __nonzero__(self): return self.__bool__() # py <3
    def __bool__(self):
        return self.offset < self.length


class UnlinkedTagTokenizer(object):
    """This will go through an html block of code and return pieces that aren't
    linked (between <a> and </a>), allowing you to mess with the blocks of plain
    text that isn't special in some way"""

    def __init__(self, text):
        self.s = Scanner(text)

    def __iter__(self):
        """returns plain text blocks that aren't in html tags"""
        start_set = set(["<a ", "<pre>", "<pre "])
        stop_set = set(["</a>", "</pre>"])

        s = self.s
        tag = ""
        plain = s.to("<")
        while s:
            yield tag, plain

            tag = s.until(">")
            plain = s.to("<")
            if [st for st in start_set if tag.startswith(st)]:
            #if tag.startswith("<a"):
                # get rid of </a>, we can't do anything with the plain because it
                # is linked in an <a> already
                #while not tag.endswith("</a>"):
                while len([st for st in stop_set if tag.endswith(st)]) == 0:
                    tag += plain
                    tag += s.until(">")
                    plain = s.to("<")

        # pick up any stragglers
        yield tag, plain


class LinkifyPostprocessor(Postprocessor):
    """This goes through and linkes any plain links in the body of the html

    other linkify example: https://github.com/Jaymon/Montage/blob/master/plugins/Utilities/src/Str.php
    """

    # http://daringfireball.net/2010/07/improved_regex_for_matching_urls
    LINKIFY_RE = re.compile(r'''\b
      (                           # Capture 1: entire matched URL
        (?:
          [a-z][\w-]+:                # URL protocol and colon
          (?:
            /{1,3}                        # 1-3 slashes
            |                             #   or
            [a-z0-9%]                     # Single letter or digit or %
                                          # (Trying not to match e.g. "URI::Escape")
          )
          |                           #   or
          www\d{0,3}[.]               # "www.", "www1.", "www2." … "www999."
          |                           #   or
          [a-z0-9.\-]+[.][a-z]{2,4}/  # looks like domain name followed by a slash
        )
        (?:                           # One or more:
          [^\s()<>]+                      # Run of non-space, non-()<>
          |                               #   or
          \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
        )+
        (?:                           # End with:
          \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
          |                                   #   or
          [^\s`!()\[\]{};:\'".,<>?«»“”‘’]        # not a space or one of these punct chars
        )
      )''', re.I | re.X)

    def run(self, text):

        def repl(m):
            return '<a class="embed" href="{}">{}</a>'.format(m.group(0), m.group(0))

        bits = []
        s = UnlinkedTagTokenizer(text)
        for tag, plain in s:
            plain_linked, made = self.LINKIFY_RE.subn(
                repl, # r'<a class="embed" href="\0">\0</a>',
                plain
            )
            bits.extend([tag, plain_linked])

        text_linked = "".join(bits)
        return text_linked


class BlockProcessor(BaseBlockProcessor):
    """
    https://github.com/waylan/Python-Markdown/blob/master/markdown/blockparser.py
    """
    def get_figure(self, parent, name):
        if self.parser.markdown.output_format in ["html5"]:
            figure = util.etree.SubElement(parent, 'figure')
            figure.set("class", "embed {}".format(name))

        else:
            figure = util.etree.SubElement(parent, 'div')
            figure.set("class", "embed figure {}".format(name))

        return figure


class YoutubeProcessor(BlockProcessor):
    """This will convert a plain youtube link to an embedded youtube video

    fun fact, this is based on some super old php code I wrote for noopsi.com 11
    years ago
    """
    def get_ytid(self, block):
        m = re.search(r"v=([^&]*)", block)
        return m.group(1) if m else None

    def test(self, parent, block):
        return re.match(r"^https?:\/\/(?:www\.)?youtube\.", block, flags=re.I) and self.get_ytid(block)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        ytid = self.get_ytid(block)
        if ytid:
            attrs = 'width="{}" height="{}" frameborder="0" allowfullscreen'.format(560, 315)
            embed_html = '<iframe {} src="https://www.youtube.com/embed/{}"></iframe>'.format(attrs, ytid)

        figure = self.get_figure(parent, "youtube")
        placeholder = self.parser.markdown.htmlStash.store(embed_html)
        figure.text = placeholder


class TwitterProcessor(BlockProcessor):
    """
    https://dev.twitter.com/rest/reference/get/statuses/oembed
    https://dev.twitter.com/web/embedded-tweets
    """
    filename = "twitter.json"

    base_url = "https://publish.twitter.com/oembed"

    regex = re.compile(r"^\S+:\/\/(?:[^\.]+\.)?twitter\.[^\/]+\/.+$")

    name = "twitter"

    def __init__(self, md, embed):
        self.embed = embed
        super(TwitterProcessor, self).__init__(md)

    def get_directory(self):
        return Directory(self.embed.getConfig("cache_dir"))

    def read_cache(self):
        d = self.get_directory()
        contents = d.file_contents(self.filename)
        cache = {}
        if contents:
            cache = json.loads(contents)
        return cache

    def write_cache(self, cache):
        d = self.get_directory()
        contents = json.dumps(cache)
        d.create_file(self.filename, contents)

    def get_response(self, url, **params):
        html = ""
        body = {}

        params["url"] = url
        res = requests.get(self.base_url, params=params)

        if res.status_code >= 200 and res.status_code < 400:
            body = res.json()
            html = body["html"]

        return html, body

    def test(self, parent, block):
        return self.regex.match(block.strip())

    def run(self, parent, blocks):
        url = blocks.pop(0).strip()
        cache = self.read_cache()

        # first we check cache, if it isn't in cache then we query twitter
        if url not in cache:
            logger.warning("Embed for {} was not in cache".format(url))

            html, body = self.get_response(url)
            if html:
                cache[url] = body
                self.write_cache(cache)

            else:
                logger.error("Embed for {} failed with code {}".format(url, res.status_code))

        # if we have the contents then we can load them up
        if url in cache:
            figure = self.get_figure(parent, self.name)
            placeholder = self.parser.markdown.htmlStash.store(cache[url]["html"])
            figure.text = placeholder


class InstagramProcessor(TwitterProcessor):
    """
    https://www.instagram.com/developer/embedding/

    https://help.instagram.com/513918941996087
    http://blog.instagram.com/post/55095847329/introducing-instagram-web-embeds
    """

    filename = "instagram.json"

    base_url = "https://api.instagram.com/oembed"

    name = "instagram"

    regex = re.compile(r"""
        ^\S+:\/\/
            (?:
                (?:[^\.]+\.)?instagram\.[^\/]+
                |
                instagr\.am
            )
            \/.+
        $
        """,
        re.I | re.X
    )

    def get_response(self, url, **params):
        params.setdefault("hidecaption", "true")
        html, body = super(InstagramProcessor, self).get_response(url, **params)

        if html:
            # let's grab the raw image and cache that also
            m = re.search(r"\/p\/([^\/\?]+)", url)
            if m:
                igid = m.group(1)
                d = self.get_directory()

                cached_image = d.files(r"^{}".format(igid))
                if cached_image:
                    logger.info("Image cached at {}".format(cached_image[0]))

                else:
                    raw_url = "https://instagram.com/p/{}/media/".format(igid)
                    res = requests.get(raw_url, params={"size": "l"})

                    if res.status_code >= 200 and res.status_code < 400:
                        ext = "jpg"
                        content_type = res.headers.get("content-type", "")
                        if content_type:
                            # ugh, mimetypes.guess_extension() returned "jpe", ugh
                            ext = content_type.split("/")[-1].lower()
                            if ext == "jpeg":
                                ext = "jpg"

                        d.create_file("{}.{}".format(igid, ext), res.content, binary=True)

                    else:
                        logger.error("Raw cache for {} failed with code {}".format(url, res.status_code))

        return html, body


class VimeoProcessor(BlockProcessor):
    """This will convert a plain vimeo link to an embedded vimeo video

    fun fact, this is based on some super old php code I wrote for noopsi.com 11
    years ago
    """
    def get_vid(self, block):
        m = re.search(r"\.com/(\d+)/?$", block)
        return m.group(1) if m else None

    def test(self, parent, block):
        block = block.strip()
        return ("vimeo" in block.lower()) and self.get_vid(block)

    def run(self, parent, blocks):
        block = blocks.pop(0).strip()
        vid = self.get_vid(block)
        if vid:
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
                '<iframe src="https://player.vimeo.com/video/{}" {}>'.format(vid, " ".join(attrs)),
                '</iframe>'
            ])

            figure = self.get_figure(parent, "vimeo")
            placeholder = self.parser.markdown.htmlStash.store(embed_html)
            figure.text = placeholder


class ImageProcessor(BlockProcessor):
    """This will take a plain link to an image and convert it into an <img> tag

    it only works on links that end with an image extension like .jpg
    """
    regex = re.compile(r"^(?:[^\s\]\[\:<>]+|\https?\:\/\/\S+?)\.(?:jpe?g|gif|bmp|png|ico|tiff)$", re.I)

    def test(self, parent, block):
        block = block.strip()
        return self.regex.match(block)

    def run(self, parent, blocks):
        block = blocks.pop(0).strip()
        figure = self.get_figure(parent, "image")
        figure.text = '![{}]({} "")'.format(os.path.basename(block), block)
        # $ret_html = '<a href="'.$url.'"><img src="'.$url.'"'.$dimension_attr.' alt="'.$url.'" /></a>';


class EmbedExtension(Extension):
    """This will embed youtube, twitter, or raw links.

    to embed a Youtube or tweet you should put the link on its own line:

        text before

        https://twitter.com/foo/status/100

        text after

    Any link that isn't already wrapped in an <a> tag will be wrapped in an <a> tag
    automatically
    """
    def __init__(self, *args, **kwargs):

        self.config = {
            'cache_dir': [
                tempfile.gettempdir(),
                "the directory where embed data can be saved"
            ],
        }
        super(EmbedExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.postprocessors.add("embed", LinkifyPostprocessor(md), "_end")
        md.parser.blockprocessors.add("embed_youtube", YoutubeProcessor(md.parser), "<paragraph")
        md.parser.blockprocessors.add("embed_twitter", TwitterProcessor(md.parser, self), "<paragraph")
        md.parser.blockprocessors.add("embed_instagram", InstagramProcessor(md.parser, self), "<paragraph")
        md.parser.blockprocessors.add("embed_vimeo", VimeoProcessor(md.parser), "<paragraph")
        md.parser.blockprocessors.add("embed_image", ImageProcessor(md.parser), "<paragraph")


def makeExtension(*args, **kwargs):
    return EmbedExtension(*args, **kwargs)

