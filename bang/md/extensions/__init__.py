# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
"""
in this package, we fix all the things I don't like about a vanilla markdown, you
can look at the individual modules to see all the goodies

Extension api: https://python-markdown.github.io/extensions/api/

extension for the markdown lib I use: https://github.com/waylan/Python-Markdown

https://github.com/Python-Markdown/markdown/tree/master/markdown/extensions
https://python-markdown.github.io/extensions/api/#registry
https://github.com/Python-Markdown/markdown/wiki/Third-Party-Extensions
https://python-markdown.github.io/extensions/
"""

from markdown.extensions import Extension as BaseExtension
from markdown.treeprocessors import Treeprocessor as BaseTreeprocessor
from markdown.postprocessors import Postprocessor as BasePostprocessor
from markdown.blockprocessors import BlockProcessor as BaseBlockprocessor
import xml.etree.ElementTree as etree


class Postprocessor(BasePostprocessor):
    def run(self, text):
        raise NotImplementedError()


class Blockprocessor(BaseBlockprocessor):
    """Fixes differences between BlockProcessor and the other extension processors

    https://github.com/Python-Markdown/markdown/blob/master/markdown/blockprocessors.py#L61
    https://python-markdown.github.io/extensions/api/#blockparser
    """
    def __init__(self, md):
        """For some reason the vanilla BlockParser takes a parser instead of a 
        Markdown instance like every other processor, so this normalizes that so
        it acts like all the others"""
        self.md = md
        super(Blockprocessor, self).__init__(md.parser)

    def test(self, parent, block):
        raise NotImplementedError()

    def run(self, parent, blocks):
        raise NotImplementedError()


class Treeprocessor(BaseTreeprocessor):
    """
    http://effbot.org/zone/pythondoc-elementtree-ElementTree.htm
    https://python-markdown.github.io/extensions/api/#treeprocessors
    https://github.com/waylan/Python-Markdown/blob/master/markdown/treeprocessors.py
    https://python-markdown.github.io/extensions/api/#working_with_et
    http://effbot.org/zone/element-index.htm#documentation
    """
    def dump(self, elem):
        """dump elem to stdout to debug"""
        return etree.dump(elem)

    def get_tags(self, elem, *tags):
        """go through and return all the *tags elements that are children of elem"""

        if len(tags) == 1:
            it = elem.iter(tags[0])
            tags = set()

        else:
            it = elem.iter()
            tags = set(tags)

        for child in it:
            #pout.v(child.tag, tags, child.tag in tags)
            if not tags or (child.tag in tags):
                yield child

    def run(self, doc):
        raise NotImplementedError()


class Extension(BaseExtension):
    """
    https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/__init__.py
    """
    def extendMarkdown(self, md):
        raise NotImplementedError()

