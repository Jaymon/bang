# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re
import tempfile
import json
import os

from markdown import util
from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor
from markdown.blockprocessors import BlockProcessor
import requests

from ...path import Directory
from ... import echo


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


class YoutubeProcessor(BlockProcessor):
    """This will convert a plain youtube link to an embedded youtube video

    fun fact, this is based on some super old php code I wrote for noopsi.com 11
    years ago
    """
    def get_ytid(self, block):
        m = re.search("v=([^&]*)", block)
        return m.group(1) if m else None

    def test(self, parent, block):
        return ("youtube" in block.lower()) and self.get_ytid(block)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        ytid = self.get_ytid(block)
        if ytid:
            dimension_attr = 'width="{}" height="{}"'.format(425, 344)

            embed_html = "\n".join([
                '<object {}>'.format(dimension_attr),
                '<param name="movie" value="http://www.youtube.com/v/{}&showsearch=0&fs=1">'.format(ytid),
                '</param><param name="wmode" value="transparent">',
                '</param><embed src="http://www.youtube.com/v/{}" type="application/x-shockwave-flash"'.format(ytid),
                'wmode="transparent" {} allowfullscreen="true"></embed></object>'.format(dimension_attr)
            ])

        figure = util.etree.SubElement(parent, 'figure')
        placeholder = self.parser.markdown.htmlStash.store(embed_html)
        figure.text = placeholder


class TwitterProcessor(BlockProcessor):
    """
    https://dev.twitter.com/rest/reference/get/statuses/oembed
    """
    def __init__(self, md, embed):
        self.embed = embed
        self.base_url = "https://publish.twitter.com/oembed"
        self.filename = "twitter.json"
        super(TwitterProcessor, self).__init__(md)

    def read_cache(self):
        d = Directory(self.embed.getConfig("cache_dir"))
        contents = d.file_contents(self.filename)
        cache = {}
        if contents:
            cache = json.loads(contents)
        return cache

    def write_cache(self, cache):
        d = Directory(self.embed.getConfig("cache_dir"))
        contents = json.dumps(cache)
        d.create_file(self.filename, contents)

    def test(self, parent, block):
        return re.match("^\S+:\/\/(?:[^\.]\.)?twitter\.[^\/]+\/.+$", block.strip())

    def run(self, parent, blocks):
        block = blocks.pop(0).strip()
        cache = self.read_cache()

        # first we check cache, if it isn't in cache then we query twitter
        if block not in cache:
            echo.out("Twitter embed for {} was in cache", block)

            params = {
                "url": block
            }
            res = requests.get(self.base_url, params=params)

            if res.status_code >= 200 and res.status_code < 400:
                cache[block] = res.json()
                self.write_cache(cache)

            else:
                echo.err("Twitter embed for {} failed with code {}", block, res.status_code)

        # if we have the contents then we can load them up
        if block in cache:
            figure = util.etree.SubElement(parent, 'figure')
            placeholder = self.parser.markdown.htmlStash.store(cache[block]["html"])
            figure.text = placeholder


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


def makeExtension(*args, **kwargs):
    return EmbedExtension(*args, **kwargs)

