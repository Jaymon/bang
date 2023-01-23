# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import re

from . import Extension, Treeprocessor
#from markdown.extensions import Extension
#from markdown.treeprocessors import Treeprocessor


class AbsoluteLinkTreeprocessor(Treeprocessor):
    """
    support for AbsoluteLinkExtension

    http://effbot.org/zone/pythondoc-elementtree-ElementTree.htm
    https://github.com/waylan/Python-Markdown/blob/master/markdown/treeprocessors.py
    """
    def normalize_url(self, url):
        """normalizes the url into a full url"""
        p = self.md.page
        return p.absolute_url(url)

    def run(self, doc):
        for elem in self.get_tags(doc, "a", "img"):
            normalize = True
            if elem.tag == 'a':
                attr_name = "href"

                # filter out footnotes since those aren't really meant to be linked
                class_name = elem.get("class")
                if class_name and class_name.lower().startswith("footnote-"):
                    normalize = False

            elif elem.tag == 'img':
                attr_name = "src"

            else:
                raise ValueError("why is absolute link dealing with {} tag?".format(elem.tag))

            if normalize:
                attr_val = elem.get(attr_name)
                url = self.normalize_url(attr_val)
                elem.set(attr_name, url)


class AbsoluteLinkExtension(Extension):
    """
    this will modify all a.href/img.src attributes to be full url paths

    if it is an http://... url, nothing happens, if it is a path.ext then it
    will be converted to a full url (http://domain.com/relative/path.ext), and if
    it is a /full/path then it will be converted to http://domain.com/full/path
    """
    def extendMarkdown(self, md):
        md.register(self, AbsoluteLinkTreeprocessor(md), "_end")

