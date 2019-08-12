# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
"""
in this package, we fix all the things I don't like about a vanilla markdown, you
can look at the individual modules to see all the goodies, and you can check out

    generator.Post.normalize_md()

to see how they are instantiated.

Extension api: https://python-markdown.github.io/extensions/api/

extension for the markdown lib I use: https://github.com/waylan/Python-Markdown

# https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/__init__.py
https://python-markdown.github.io/extensions/api/#registry
https://github.com/Python-Markdown/markdown/wiki/Third-Party-Extensions
https://python-markdown.github.io/extensions/
"""

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor as BaseTreeprocessor


class Treeprocessor(BaseTreeprocessor):
    """
    http://effbot.org/zone/pythondoc-elementtree-ElementTree.htm
    https://github.com/waylan/Python-Markdown/blob/master/markdown/treeprocessors.py
    """
    def get_tags(self, elem, *tags):
        """go through and return all the *tags elements that are children of elem"""
        tags = set(tags)
        for child in elem.getiterator():
            #pout.v(child.tag, tags, child.tag in tags)
            if child.tag in tags:
                yield child


# class Extension(BaseExtension):
#     """
#     https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/__init__.py
#     """
#     def find_priority(self, registry, names=None, priority=0):
#         """compensates for Markdown's 3.0 branch deprecation and bug in md.preprocessors.add()
#         method
# 
#         https://python-markdown.github.io/extensions/api/#extendmarkdown
#         """
# 
#         if names:
#             position = ""
#             for name in names:
#                 if name in registry:
#                     index = registry.get_index_for_name(name)
#                     priority = registry._priority[index][1] + 1
#                     break
# 
#         else:
#             priority = 0
#             for t in registry._priority:
#                 priority = max(t[1], priority)
# 
#             priority += 1
# 
#         return priority
# 
