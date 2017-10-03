# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension


class Sub(object):
    def __init__(self, placeholder):
        self.index = 1
        self.placeholder = placeholder
        self.link_placeholders = []
        self.footnote_placeholders = []
        # TODO -- make this better, it should do [^n] anywhere but only [n] if
        # proceeded by ]
        #self.regex = re.compile(r"\[\^?({})\](?!:)".format(placeholder))
        #self.footnote_regex = re.compile(r"(?:(?:\[\^{}\])|(?:(?<=\])\[{}]n\]))(?!:)".format(placeholder, placeholder))
        self.link_regex = re.compile(r"(?<=\])\[{}\](?!:)".format(placeholder))
        self.def_link_regex = re.compile(r"^\[{}]:".format(placeholder))

        self.footnote_regex = re.compile(r"\[\^{}\](?!:)".format(placeholder))
        self.def_footnote_regex = re.compile(r"^\[\^{}\]:".format(placeholder))

    def callback(self, m):
        fn_id = "^" if "^" in m.group(0) else ""
        ret = "[{}magicref-{}-{}]".format(fn_id, self.placeholder, self.index)
        if fn_id:
            self.footnote_placeholders.append(ret)
        else:
            self.link_placeholders.append(ret)

        self.index += 1
        return ret

    def def_callback(self, m):
        fn_id = "^" if "^" in m.group(0) else ""
        if fn_id:
            ret = self.footnote_placeholders.pop(0)
        else:
            ret = self.link_placeholders.pop(0)
        return ret + ":"

    def sub(self, line):
        ret = self.link_regex.sub(self.callback, line)
        ret = self.def_link_regex.sub(self.def_callback, ret)

        ret = self.footnote_regex.sub(self.callback, ret)
        ret = self.def_footnote_regex.sub(self.def_callback, ret)
        return ret


class MagicRefPreprocessor(Preprocessor):
    def __init__(self, md, config):
        super(MagicRefPreprocessor, self).__init__(md)
        self.config = config

    def run(self, lines):
        placeholder = self.config["EASY_PLACEHOLDER"]
        s = Sub(self.config["EASY_PLACEHOLDER"])
        #placeholders = []

        #regex = re.compile(r"\[\^?({})\](?!:)".format(placeholder))
        #def_regex = re.compile(r"^\[\^?({})\]:".format(placeholder))
#         i = 1
#         def callback(m):
#             ret = "[magicref-{}-{}]".format(placeholder, i)
#             placeholders.append(ret)
#             i += 1
#             return ret

        ret = []
        for line in lines:
#             new_line = s.regex.sub(s.callback, line)
#             new_line = s.def_regex.sub(s.def_callback, new_line)
            ret.append(s.sub(line))



#             ms = regex.findall(line)
#             for m in ms:
#                 pout.v(m.group(1), m.start, m.stop)

#         new_lines = []
#         for line in lines:
#             m = MYREGEX.match(line)
#             if m:
#                 # do stuff
#             else:
#                 new_lines.append(line)
        #pout.v(ret)

        if len(s.footnote_placeholders) > 0:
            raise RuntimeError("Mismatched magic footnotes")
        if len(s.link_placeholders) > 0:
            raise RuntimeError("Mismatched magic links")

        return ret


class MagicRefExtension(Extension):
    def __init__(self, *args, **kwargs):
        super(MagicRefExtension, self).__init__(*args, **kwargs)
        self.config.setdefault(
            "EASY_PLACEHOLDER",
            ["n", "the text string that marks autoincrement footers"]
        )

    def extendMarkdown(self, md, md_globals):
        # Insert instance of 'mypattern' before 'references' pattern
        position = '<reference'
        if "footnote" in md.preprocessors:
            position = '<footnote'

        md.preprocessors.add('magicref', MagicRefPreprocessor(md, self.getConfigs()), position)

