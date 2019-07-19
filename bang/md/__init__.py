# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.footnotes import FootnoteExtension

from .extensions.delins import DelInsExtension
#from .extensions.domevent import DomEventExtension
from .extensions.absolutelink import AbsoluteLinkExtension
from .extensions.image import ImageExtension
from .extensions.highlight import HighlightExtension
from .extensions.magicref import MagicRefExtension
from .extensions.reference import RefPositionFixExtension
from .extensions.embed import EmbedExtension


class Markdown(markdown.Markdown):
    """
    https://github.com/Python-Markdown/markdown/blob/master/markdown/__init__.py
    """
    instance = None

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = cls.create_instance()
        return cls.instance

    @classmethod
    def create_instance(cls):
        return cls(
            extensions=[
                # as of Markdown 3.0+ order can matter
                FootnoteExtension(UNIQUE_IDS=True, SEPARATOR="-"),
                MagicRefExtension(),
                RefPositionFixExtension(),
                HighlightExtension(),
                'tables',
                'nl2br',
                'attr_list',
                #'smart_strong',
                'meta', # http://pythonhosted.org/Markdown/extensions/meta_data.html
                'admonition', # https://pythonhosted.org/Markdown/extensions/admonition.html
                TocExtension(baselevel=1), # https://pythonhosted.org/Markdown/extensions/toc.html
                ImageExtension(),
                DelInsExtension(),
                AbsoluteLinkExtension(),
                #DomEventExtension(),
                EmbedExtension(),
            ],
            output_format="html"
        )

    def reset(self):
        super(Markdown, self).reset()
        self.dirtype = None

    def output(self, dirtype):
        self.reset()
        self.dirtype = dirtype
        return self.convert(dirtype.body)

#     def convert(self, source):
#         """This is the method that all the magic happens, so if you need to start peering
#         into the internals of markdown parsing the file and doing its thing I would
#         just copy this whole method from:
# 
#         https://github.com/Python-Markdown/markdown/blob/master/markdown/__init__.py#L332
# 
#         and then mess with it as you see fit, I'm leaving this method/comment here so
#         I'll remember for the future
#         """
#         pass

