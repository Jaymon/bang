# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import re

from markdown import util
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.inlinepatterns import ImagePattern as BaseImagePattern, \
    ImageReferencePattern as BaseImageReferencePattern
from markdown.inlinepatterns import LINK_RE, IMAGE_LINK_RE, \
    REFERENCE_RE, IMAGE_REFERENCE_RE

from .absolutelink import AbsoluteLinkTreeprocessor


class ImageTreeprocessor(AbsoluteLinkTreeprocessor):
    """support for ImageExtension, this just goes through and makes sure any img
    element in a figure element has a figcaption if the img element has a title
    attribute"""
    def run(self, doc):
        for elem in self.get_tags(doc, "figure"):
            for child in self.get_tags(elem, "img"):
                title = child.get("title")
                if title:
                    figcaption = util.etree.SubElement(child, 'figcaption')
                    figcaption.text = title


class ImagePattern(BaseImagePattern):
    """over-rides parent to swap alt with title if title is empty and then use
    the basename of src as the alt"""
    def handleMatch(self, m):
        el = super(ImagePattern, self).handleMatch(m)
        if el is not None:
            title = el.get("title")
            if not title:
                alt = el.get("alt")
                if alt:
                    el.set("title", alt)
                src = el.get("src")
                el.set("alt", os.path.basename(src))

        return el


class ImageReferencePattern(BaseImageReferencePattern):
    """over-rides parent to swap alt with title if title is empty and then use
    the basename of src as the alt"""
    def makeTag(self, href, title, text):
        if not title:
            title = text
            text = os.path.basename(href)
        return super(ImageReferencePattern, self).makeTag(href, title, text)


class ImageProcessor(BlockProcessor):
    def test(self, parent, block):
        # TODO -- if this proves brittle then import the inline parser stuff and use those regexes
        regex = r"^\s*!\[[^\]]*\]" # we need to match ![]
        regex += r"(?:" # start block
        regex += r"\([^\)\(]+\)" # look for ()
        regex += r"|"
        regex += r"\[[^\]\[]+\]" # otherwise look for []
        regex += r")" # close block
        regex += r"\s*$"
        return re.match(regex, block)
        #return block.startswith("![") and (block.endswith("]") or block.endswith(")"))

#from markdown.inlinepatterns import LINK_RE, IMAGE_LINK_RE, \
#    REFERENCE_RE, IMAGE_REFERENCE_RE



    def run(self, parent, blocks):
        #pout.v(blocks)
        block = blocks.pop(0)
        # TODO -- check markdown for html5 content_type
        figure = util.etree.SubElement(parent, 'figure')
        figure.text = block.strip()


class ImageExtension(Extension):
    """
    this looks at img tags and makes sure they are centered if they are solo or floating
    if they are in paragraph's with content, this also loosens markdown parsing so
    something like:

        ![title text](name.jpg)

    will set "title text" to the title attribute instead of the alt attribute, the
    alt tag will be set with the basename of the image, this just makes the markdown
    syntax have a bit less cognitive overhead, if you specify a title it will use
    that instead, so ![alt](name.jpg "title text") would still work
    """
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.processor = ImageTreeprocessor()
        #md.treeprocessors.add('href', self.processor, ">")
        md.treeprocessors['image'] = self.processor

        md.inlinePatterns["image_link"] = ImagePattern(
            md.inlinePatterns["image_link"].pattern,
            md
        )
        md.inlinePatterns["image_reference"] = ImageReferencePattern(
            md.inlinePatterns["image_reference"].pattern,
            md
        )

        md.parser.blockprocessors.add(
            "image", ImageProcessor(md.parser), "<paragraph"
        )


