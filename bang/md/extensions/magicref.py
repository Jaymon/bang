# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

from markdown.preprocessors import Preprocessor
from . import Extension


class Sub(object):
    """where all the magic happens, the other classes are mainly boilerplate and
    configuration, this class does the actual searching and replacing of the refs
    """
    def __init__(self, placeholder):
        self.index = 1
        self.placeholder = placeholder
        self.link_placeholders = []
        self.footnote_placeholders = []

        self.link_regex = re.compile(r"(?<=\])\[{}\]".format(placeholder))
        self.def_link_regex = re.compile(r"^\[{}]:".format(placeholder))

        self.footnote_regex = re.compile(r"(?<!^)\[\^{}\]".format(placeholder))
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

        # this ignores inline codeblocks from being evaluated
        def bits(line):
            chars = []
            ignore = False
            for c in line:
                if c == '`':
                    if ignore:
                        chars.append(c)
                        yield "".join(chars), ignore
                        chars = []
                        ignore = False
                    else:
                        yield "".join(chars), ignore
                        chars = [c]
                        ignore = True
                else:
                    chars.append(c)

            yield "".join(chars), ignore


        ret = []
        for bit, ignore in bits(line):
            if ignore:
                ret.append(bit)
            else:
                bit = self.link_regex.sub(self.callback, bit)
                bit = self.def_link_regex.sub(self.def_callback, bit)

                bit = self.footnote_regex.sub(self.callback, bit)
                bit = self.def_footnote_regex.sub(self.def_callback, bit)

                ret.append(bit)

        return "".join(ret)


class MagicRefPreprocessor(Preprocessor):
    """This is the preprocessor extension class that will look through the lines
    passed into run and munge them to have unique references if it finds magic
    references in the line"""
    def __init__(self, md, config):
        super(MagicRefPreprocessor, self).__init__(md)
        self.config = config

    def run(self, lines):
        ret = []
        placeholder = self.config["EASY_PLACEHOLDER"]
        s = Sub(self.config["EASY_PLACEHOLDER"])
        for line in lines:
            # TODO -- this should skip ``` codeblocks
            ret.append(s.sub(line))

        if len(s.footnote_placeholders) > 0:
            raise RuntimeError("Mismatched magic footnotes")
        if len(s.link_placeholders) > 0:
            raise RuntimeError("Mismatched magic links")

        return ret


class MagicRefExtension(Extension):
    """
    creates an easy footnote where you can just use [^n] for each of the footnotes
    and if you just make sure your definitions are in order then everything will work.
    While this isn't compatible with other markdown it makes it easier for me to write
    posts, and I'm all about removing friction in blog posts

    this also allows all reference links to just be a placeholder (eg, [n]) and as
    long as they are in order the correct link will be associated with the correct <a> tag
    """
    def __init__(self, *args, **kwargs):
        super(MagicRefExtension, self).__init__(*args, **kwargs)
        self.config.setdefault(
            "EASY_PLACEHOLDER",
            ["n", "the text string that marks magic references"]
        )

    def extendMarkdown(self, md, md_globals):

        priority = self.find_priority(md.preprocessors, ["footnote", "reference"])
        md.preprocessors.register(MagicRefPreprocessor(md, self.getConfigs()), "magicref", priority)



#         position = ""
#         if "footnote" in md.preprocessors:
#             position = "footnote"
#         elif "reference" in md.preprocessors:
#             position = "reference"
# 
#         priority = 100
#         if position:
#             priority = md.preprocessors._priority[md.preprocessors.get_index_for_name(position)][1] + 1
# 
# #         position = '<reference'
# #         if "footnote" in md.preprocessors:
# #             position = '<footnote'
#         #md.preprocessors.add('magicref', MagicRefPreprocessor(md, self.getConfigs()), position)
# 
#         md.preprocessors.register(MagicRefPreprocessor(md, self.getConfigs()), "magicref", priority)

