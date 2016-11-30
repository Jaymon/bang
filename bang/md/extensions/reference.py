# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from markdown.extensions.footnotes import FootnoteExtension as BaseFootnoteExtension, \
    FootnotePattern as BaseFootnotePattern


class FootnotePattern(BaseFootnotePattern):
    def handleMatch(self, m):
        """This differs from parent by just incrementing footnotes.match_id if the
        placeholder was used, otherwise is is transparent
        """
        id = m.group(2)
        m_id = m

        placeholder = self.footnotes.getConfig("EASY_PLACEHOLDER")
        if id == placeholder:
            class MatchId(object):
                def __init__(self, id):
                    self.id = id
                def group(self, *args):
                    return self.id

            m_id = MatchId(self.footnotes.matched_id)
            self.footnotes.matched_id += 1

        return super(FootnotePattern, self).handleMatch(m_id)


class PlaceholderDict(dict):
    """Small wrapper around a dict that monitors set/get/contains for a placeholder
    key and if it sees it then it will change that key to an auto-increment key
    and return the matching internal key, basically, it allows you to do something
    like:
        d = PlaceholderDict("foo")
        d["foo"] = 1
        d["foo"] = 2

    and save both 1 and 2 in the dict. It only works for setitem/getitem/contains though, 
    so you can't do d.get("foo") and have it work

    NOTE -- for when I try to make FootnoteExtension use this again, you would need
        this to extend orderedDict, and also you would need an placeholder_index_i
        instance variable, and you would need to handle .keys() and .index() calls
        successfully, then I think it would work (see the original FootnotePattern
        for where these are used)
    """
    def __init__(self, placeholder, *args, **kwargs):
        super(PlaceholderDict, self).__init__(*args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_set_i = 1
        self.placeholder_get_i = 1

    def get_key(self, k, placeholder_i):
        if k == self.placeholder:
            k = "{}-{}".format(self.placeholder, placeholder_i)
        return k

    def __setitem__(self, k, v):
        nk = self.get_key(k, self.placeholder_set_i)
        self.placeholder_set_i += 1
        super(PlaceholderDict, self).__setitem__(nk, v)

    def __getitem__(self, k):
        nk = self.get_key(k, self.placeholder_get_i)
        self.placeholder_get_i += 1
        return super(PlaceholderDict, self).__getitem__(nk)

    def __contains__(self, k):
        nk = self.get_key(k, self.placeholder_get_i)
        return super(PlaceholderDict, self).__contains__(nk)


class FootnoteExtension(BaseFootnoteExtension):
    """
    This extends the included footnote extension and allows an easy footnote where
    you can just use [^n] for each of the footnotes and if you just make sure your
    definitions are in order then everything will work. While this isn't compatible with
    other markdown it makes it easier for me to write posts, and I'm all about
    removing friction in blog posts

    https://github.com/waylan/Python-Markdown/blob/master/markdown/extensions/footnotes.py
    """
    def __init__(self, *args, **kwargs):
        super(FootnoteExtension, self).__init__(*args, **kwargs)
        self.config.setdefault(
            "EASY_PLACEHOLDER",
            ["n", "the text string that marks autoincrement footers"]
        )

    def extendMarkdown(self, md, md_globals):
        """ Add pieces to Markdown. """
        super(FootnoteExtension, self).extendMarkdown(md, md_globals)

        # what we do here is we allow the parent to configure everything and then
        # we just go in and replace the pattern matcher with our own, silently, like a ninja
        # https://github.com/waylan/Python-Markdown/blob/master/markdown/inlinepatterns.py
        md.inlinePatterns["footnote"] = FootnotePattern(md.inlinePatterns["footnote"].pattern, self)

    def reset(self):
        super(FootnoteExtension, self).reset()
        self.found_id = 1
        self.matched_id = 1

    def setFootnote(self, id, text):
        """This differs from parent by using our own id if passed in id matches
        our placeholder, otherwise it is transparent"""
        found_id = id
        placeholder = self.getConfig("EASY_PLACEHOLDER")
        if id == placeholder:
            found_id = self.found_id
            self.found_id += 1

        return super(FootnoteExtension, self).setFootnote(found_id, text)


class ReferenceExtension(FootnoteExtension):
    """Similar to the FootnoteExtension, this allows all reference links to just be
    a placeholder (eg, [n]) and as long as they are in order the correct link will
    be associated with the correct a tag"""
#     def __init__(self, *args, **kwargs):
#         self.config = {
#             "EASY_PLACEHOLDER": ["n", "the text string that marks autoincrement references"],
#         }
#         super(ReferenceExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        super(ReferenceExtension, self).extendMarkdown(md, md_globals)

        # we just replace the standard references dict with our implementation
        # and then let the builtin plugins do all the heavy lifting
        md.references = PlaceholderDict(self.getConfig("EASY_PLACEHOLDER"))


# from markdown.inlinepatterns import ImagePattern as BaseImagePattern
# 
# class ImagePattern(BaseImagePattern):
#     def handleMatch(self, m):
#         el = super(ImagePattern, self).handleMatch(m)
#         if el:
#             pout.v(el)
#         return el
# 
# 
# class ImgExtension(Extension):
#     def extendMarkdown(self, md, md_globals):
#         # we just replace the standard references dict with our implementation
#         # and then let the builtin plugins do all the heavy lifting
#         md.inlinePatterns["image_link"] = ImagePattern(md.inlinePatterns["image_link"].pattern, md)
# 
