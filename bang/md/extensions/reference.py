# -*- coding: utf-8 -*-
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
    """reference definitions need a line between each definition, this
    enforces that norm

    a blank line would be placed between the `[^n]` and `[n]` lines using this
    extension

    .. Example:
        [^n]: this is the footnote
        [n]: http://link.com

        # would become:

        [^n]: this is the footnote

        [n]: http://link.com
    """
    def extendMarkdown(self, md):
        # it's best we run this before any other extension that messes with
        # references
        md.register(
            self,
            RefPositionFixPreprocessor(md),
            ["<MagicRefPreprocessor", "<footnote", "<reference"]
        )

