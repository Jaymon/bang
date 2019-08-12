# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

from markdown.preprocessors import Preprocessor
from . import Extension


class RefPositionFixPreprocessor(Preprocessor):
    def run(self, lines):
        regex = re.compile(r"^\[\^?[^\]]\]:")
        ret = []

        for line_number, line in enumerate(lines):
            if regex.match(line):
                prev_line_number = line_number - 1
                if prev_line_number > 0:
                    prev_line = lines[prev_line_number]
                    if prev_line and not prev_line.isspace():
                        ret.append("")

            ret.append(line)

        return ret


class RefPositionFixExtension(Extension):
    """reference definitions need a line between each definition, this enforces
    that norm

    :Example:
        [^n]: this is the footnote
        [n]: http://link.com

    a blank line would be placed between the `[^n]` and `[n]` lines using this extension
    """
    def extendMarkdown(self, md):
        # it's best we run this before any other extension that messes with references
        md.register(
            self,
            RefPositionFixPreprocessor(md),
            ["<MagicRefPreprocessor", "<footnote", "<reference"]
        )



#         priority = self.find_priority(md.preprocessors, ["magicref", "footnote", "reference"])
#         md.preprocessors.register(RefPositionFixPreprocessor(md), "refpositionfix", priority)

        # it's best we run this before any other extension that messes with references
#         position = '<reference'
#         if "footnote" in md.preprocessors:
#             position = '<footnote'
#         if "magicref" in md.preprocessors:
#             position = '<magicref'
# 
#         md.preprocessors.add('refpositionfix', RefPositionFixPreprocessor(md), position)

