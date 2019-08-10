# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
#from collections import defaultdict
from collections import Counter

import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.treeprocessors import Treeprocessor


from ..compat import *
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
    https://python-markdown.github.io/
    https://github.com/Python-Markdown/markdown/blob/master/docs/change_log/release-3.0.md

    extends this class:
        https://github.com/Python-Markdown/markdown/blob/master/markdown/core.py
    """
    @classmethod
    def create_extensions(cls):
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
            #'smart_strong', # removed in 3.0+
            'meta', # http://pythonhosted.org/Markdown/extensions/meta_data.html
            'admonition', # https://pythonhosted.org/Markdown/extensions/admonition.html
            TocExtension(baselevel=1), # https://pythonhosted.org/Markdown/extensions/toc.html
            ImageExtension(),
            DelInsExtension(),
            AbsoluteLinkExtension(),
            #DomEventExtension(),
            EmbedExtension(),
        ]

    @classmethod
    def create_instance(cls, config, extensions=None):
        extensions = extensions or cls.create_extensions()
        instance = cls(
            extensions=extensions,
            output_format="html"
        )
        instance.config = config
        return instance

    def __init__(self, **kwargs):
        self.registered_names = set()
        super(Markdown, self).__init__(**kwargs)

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

    def register(self, extension, api=None, priority="_end"):
        name = String(extension.__class__.__name__)

        if name not in self.registered_names:
            if api:
                self.registerExtension(extension)
                self.registered_names.add(name)
            else:
                self.registerExtensions(extensions=[extension], configs={})

        if api:
            if isinstance(api, Treeprocessor):
                registry = self.treeprocessors

            else:
                raise ValueError("Unknown extension {}".format(name))

            if isinstance(priority, int):
                registry.register(api, name, priority)

            else:
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

                registry.register(api, name, pr)


