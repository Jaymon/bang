# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
"""
in this package, we fix all the things I don't like about a vanilla markdown, you
can look at the individual modules to see all the goodies, and you can check out

    generator.Post.normalize_md()

to see how they are instantiated.

extension for the markdown lib I use: https://github.com/waylan/Python-Markdown

http://pythonhosted.org/Markdown/extensions/index.html
http://pythonhosted.org/Markdown/extensions/api.html

https://github.com/waylan/Python-Markdown/wiki/Third-Party-Extensions
"""

from markdown.extensions import Extension as BaseExtension


class Extension(BaseExtension):
    def find_priority(self, registry, names=None, priority=0):
        """compensates for Markdown's 3.0 branch deprecation and bug in md.preprocessors.add()
        method"""

        if names:
            position = ""
            for name in names:
                if name in registry:
                    index = registry.get_index_for_name(name)
                    priority = registry._priority[index][1] + 1
                    break

        else:
            priority = 0
            for t in registry._priority:
                priority = max(t[1], priority)

            priority += 1

        return priority

