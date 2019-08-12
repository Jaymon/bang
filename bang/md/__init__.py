# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
#from collections import defaultdict
from collections import Counter
import logging

import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.treeprocessors import Treeprocessor
from markdown.inlinepatterns import InlineProcessor, Pattern
from markdown.blockprocessors import BlockProcessor
from markdown.postprocessors import Postprocessor
from markdown.preprocessors import Preprocessor


from ..compat import *
from .extensions.delins import DelInsExtension
#from .extensions.domevent import DomEventExtension
from .extensions.absolutelink import AbsoluteLinkExtension
from .extensions.image import ImageExtension
from .extensions.highlight import HighlightExtension
from .extensions.magicref import MagicRefExtension
from .extensions.reference import RefPositionFixExtension
from .extensions.embed import EmbedExtension


logger = logging.getLogger(__name__)


class Markdown(markdown.Markdown):
    """
    https://github.com/Python-Markdown/markdown/blob/master/markdown/__init__.py
    https://python-markdown.github.io/
    https://github.com/Python-Markdown/markdown/blob/master/docs/change_log/release-3.0.md

    extends this class:
        https://github.com/Python-Markdown/markdown/blob/master/markdown/core.py
    """
    @classmethod
    def create_extensions(cls):
        return [HighlightExtension()]
        return [
            # as of Markdown 3.0+ order can matter
            # https://python-markdown.github.io/extensions/footnotes/
            FootnoteExtension(UNIQUE_IDS=True, SEPARATOR="-"),
            MagicRefExtension(),
            RefPositionFixExtension(),
            HighlightExtension(),
            'tables',
            'nl2br',
            'attr_list',
            'meta', # http://pythonhosted.org/Markdown/extensions/meta_data.html
            'admonition', # https://pythonhosted.org/Markdown/extensions/admonition.html
            TocExtension(baselevel=1), # https://pythonhosted.org/Markdown/extensions/toc.html
            ImageExtension(),
            DelInsExtension(),
            AbsoluteLinkExtension(),
            EmbedExtension(),
        ]

    @classmethod
    def create_instance(cls, config, extensions=None):
        extensions = extensions or cls.create_extensions()
        try:
            instance = cls(
                extensions=extensions,
                output_format="html"
            )
            instance.config = config

        except Exception as e:
            # this exception has a high chance of getting suppressed because
            # this method is usually called from a @property definition
            logger.exception(e)
            raise

        return instance

#     def __init__(self, **kwargs):
#         #self.registered_extension_names = set()
#         super(Markdown, self).__init__(**kwargs)

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

    def find_priority(self, priority, registry):

        if not isinstance(priority, int):
            if isinstance(priority, basestring):
                priority = [priority]

            pr = 0
            d = Counter()

            for p in priority:
                if p == "_begin":
                    for t in registry._priority:
                        pr = max(t[1], pr)
                    pr += 5

                elif p == "_end":
                    for t in registry._priority:
                        pr = min(t[1], pr)
                    pr -= 5

                else:
                    k = "="
                    if p.startswith("<") or p.startswith(">"):
                        k = p[0]
                        p = p[1:]

                    if p in registry:
                        index = registry.get_index_for_name(p)
                        if k == ">":
                            d[k] = min(d[k], registry._priority[index][1])
                        elif k == "<":
                            d[k] = max(d[k], registry._priority[index][1])

                        else:
                            d[k] = registry._priority[index][1]

            if ">" in d and "<" in d:
                pr = d[">"] + int(d["<"] - d[">"] / 2)

            elif ">" in d:
                pr = d[">"] - 5

            elif "<" in d:
                pr = d["<"] + 5

            elif "=" in d:
                pr = d["="]

            return pr

    def registered(self, processor):
        if isinstance(processor, Treeprocessor):
            registry = self.treeprocessors

        elif isinstance(processor, (InlineProcessor, Pattern)):
            registry = self.inlinePatterns

        elif isinstance(processor, BlockProcessor):
            registry = self.parser.blockprocessors

        elif isinstance(processor, Postprocessor):
            registry = self.postprocessors

        elif isinstance(processor, Preprocessor):
            registry = self.preprocessors

        else:
            raise ValueError("Unknown extension processor {}".format(name))

        return registry

    def register(self, extension, processor=None, priority="", **kwargs):

#         if extension_name not in self.registered_extension_names:
#             if not processor:
#                 # I have no idea why this needs to be done but all the
#                 # extensions do it so we're doing it to
#                 #self.registerExtension(extension) # 3.0 examples don't do this
#                 self.registered_extension_names.add(extension_name)
# 
#             else:
#                 # we didn't pass in a processor so we are adding this extension to
#                 # markdown
#                 self.registerExtensions(
#                     extensions=[extension],
#                     configs=kwargs.get("configs", {})
#                 )

        if processor:

            name = kwargs.get("name", String(processor.__class__.__name__))
            registry = self.registered(processor)

            if not priority:
                # if a priority wasn't passed in, we are going to check name to 
                # see if we are replacing it, if we are then we will use the
                # previous priority, if name isn't in the registry then we will
                # set priority to _end
                try:
                    index = registry.get_index_for_name(name)
                    if index:
                        priority = registry._priority[index][1]

                except ValueError:
                    priority = "_end"

            registry.register(processor, name, self.find_priority(priority, registry))

        else:
            #extension_name = String(extension.__class__.__name__)
            # we didn't pass in a processor so we are adding this extension to
            # markdown
            self.registerExtensions(
                extensions=[extension],
                configs=kwargs.get("configs", {})
            )

