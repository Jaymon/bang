# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagPattern


class DelInsExtension(Extension):
    """
    Adds delete/insert support

    ~~delete this text~~
    ++insert this text++

    I cribbed this from https://github.com/aleray/mdx_del_ins/blob/master/mdx_del_ins.py
    """
    DEL_RE = r"(\~{2})(.+?)(\~{2})"
    INS_RE = r"(\+{2})(.+?)(\+{2})"

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('del', SimpleTagPattern(self.DEL_RE, 'del'), '<not_strong')
        md.inlinePatterns.add('ins', SimpleTagPattern(self.INS_RE, 'ins'), '<not_strong')


