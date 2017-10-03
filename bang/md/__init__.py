# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import markdown
from markdown.extensions.toc import TocExtension

from .extensions.delins import DelInsExtension
from .extensions.domevent import DomEventExtension
from .extensions.absolutelink import AbsoluteLinkExtension
from .extensions.image import ImageExtension
from .extensions.highlight import HighlightExtension
from .extensions.footnote import FootnoteExtension
from .extensions.magicref import MagicRefExtension
from .extensions.embed import EmbedExtension
#from .extensions.reference import ReferenceExtension


class Markdown(markdown.Markdown):
    """
    https://github.com/Python-Markdown/markdown/blob/master/markdown/__init__.py
    """
    instance = None

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = cls(
                extensions=[
                    #ReferenceExtension(UNIQUE_IDS=True),
                    #FootnoteExtension(UNIQUE_IDS=True),
                    MagicRefExtension(),
                    HighlightExtension(),
                    'tables',
                    'nl2br',
                    'attr_list',
                    'smart_strong',
                    'meta', # http://pythonhosted.org/Markdown/extensions/meta_data.html
                    'admonition', # https://pythonhosted.org/Markdown/extensions/admonition.html
                    TocExtension(baselevel=1), # https://pythonhosted.org/Markdown/extensions/toc.html
                    ImageExtension(),
                    DelInsExtension(),
                    AbsoluteLinkExtension(self),
                    DomEventExtension(self),
                    #"bang.md.extensions.embed(cache_dir={})".format(self.directory),
                    EmbedExtension(cache_dir=self.directory),
                ],
                output_format="html5"
            )

        return cls.instance


# !!! - use this method when debugging
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

