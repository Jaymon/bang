# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from markdown.extensions.footnotes import FootnoteExtension as BaseFootnoteExtension


class FootnoteExtension(BaseFootnoteExtension):
    """

    https://github.com/waylan/Python-Markdown/blob/master/markdown/extensions/footnotes.py
    """

    unique_prefix = 0
    """We need a class property to persist across multiple instantiations"""

    def reset(self):
        super(FootnoteExtension, self).reset()
        self.found_id = 1
        self.matched_id = 1

        # fix UNIQUE_IDS that doesn't work across multiple instanciations
        type(self).unique_prefix += 1
        self.unique_prefix = type(self).unique_prefix

